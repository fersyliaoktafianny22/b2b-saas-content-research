#!/usr/bin/env python3

"""Collect recent LinkedIn posts from profile activity pages.
Use only for content you are authorized to access and in accordance withLinkedIn's terms and applicable privacy laws."""

from future import annotations

import argparseimport asyncioimport hashlibimport loggingimport reimport sysfrom dataclasses import dataclassfrom datetime import datetime, timedelta, timezonefrom pathlib import Pathfrom urllib.parse import urlsplit, urlunsplit

from playwright.async_api import (Locator,Page,TimeoutError as PlaywrightTimeoutError,async_playwright,)

LOG = logging.getLogger("linkedin-post-collector")DEFAULT_OUTPUT_DIR = Path("research/linkedin-posts")DEFAULT_USER_DATA_DIR = Path(".playwright/linkedin")

POST_CARD_SELECTORS = ("div.feed-shared-update-v2","div[data-urn^='urn:li:activity:']","article",)AUTHOR_SELECTORS = (".update-components-actor__name",".feed-shared-actor__name",)CONTENT_SELECTORS = (".update-components-text",".feed-shared-update-v2__description",".feed-shared-text",)DATE_SELECTORS = (".update-components-actor__sub-description",".feed-shared-actor__sub-description",)

@dataclass(frozen=True)class Post:author_name: strpost_date: strpost_url: strcontent: strpublished_at: datetime | None = None

def parse_args() -> argparse.Namespace:parser = argparse.ArgumentParser(description="Collect recent LinkedIn posts into one Markdown file per expert.")parser.add_argument("profiles_file",type=Path,help="Text file containing one LinkedIn profile URL per line.",)parser.add_argument("--output-dir",type=Path,default=DEFAULT_OUTPUT_DIR,help=f"Output directory (default: {DEFAULT_OUTPUT_DIR}).",)parser.add_argument("--user-data-dir",type=Path,default=DEFAULT_USER_DATA_DIR,help="Persistent Playwright profile used to retain your LinkedIn login.",)parser.add_argument("--days",type=int,default=30,help="Keep posts from the last N days when an exact date is available (default: 30).",)parser.add_argument("--max-posts",type=int,default=20,help="Maximum posts to save per expert (default: 20).",)parser.add_argument("--max-scrolls",type=int,default=12,help="Maximum page scrolls per expert (default: 12).",)parser.add_argument("--headless",action="store_true",help="Run without a visible browser. First-time login requires headed mode.",)parser.add_argument("--slow-mo",type=int,default=0,metavar="MS",help="Delay Playwright actions by this many milliseconds.",)parser.add_argument("--log-level",choices=("DEBUG", "INFO", "WARNING", "ERROR"),default="INFO",)args = parser.parse_args()for name in ("days", "max_posts", "max_scrolls"):if getattr(args, name) < 1:parser.error(f"--{name.replace('_', '-')} must be at least 1")if args.slow_mo < 0:parser.error("--slow-mo cannot be negative")return args

def normalize_profile_url(value: str) -> str:parts = urlsplit(value.strip())if parts.scheme not in {"http", "https"}:raise ValueError("URL must start with http:// or https://")if (parts.hostname or "").lower() not in {"linkedin.com", "www.linkedin.com"}:raise ValueError("URL must point to linkedin.com")path = re.sub(r"/+", "/", parts.path).rstrip("/")if not re.fullmatch(r"/in/[^/]+", path, flags=re.IGNORECASE):raise ValueError("expected a profile URL such as https://www.linkedin.com/in/name")return urlunsplit(("https", "www.linkedin.com", path, "", ""))

def load_profile_urls(path: Path) -> list[str]:if not path.is_file():raise FileNotFoundError(f"Profiles file not found: {path}")urls: list[str] = []errors: list[str] = []for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):value = raw_line.strip()if not value or value.startswith("#"):continuetry:url = normalize_profile_url(value)except ValueError as exc:errors.append(f"line {line_number}: {exc} ({value!r})")continueif url not in urls:urls.append(url)if errors:raise ValueError("Invalid profile URLs:\n  " + "\n  ".join(errors))if not urls:raise ValueError(f"No profile URLs found in {path}")return urls

def activity_url(profile_url: str) -> str:return f"{profile_url}/recent-activity/all/"

def clean_text(value: str) -> str:lines = [re.sub(r"[ \t]+", " ", line).strip() for line in value.splitlines()]return "\n".join(line for line in lines if line).strip()

def safe_filename(name: str, profile_url: str) -> str:slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")if not slug:slug = profile_url.rstrip("/").rsplit("/", 1)[-1].lower()digest = hashlib.sha256(profile_url.encode()).hexdigest()[:8]return f"{slug or 'expert'}-{digest}.md"

def parse_datetime(value: str) -> datetime | None:try:parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))except ValueError:return Noneif parsed.tzinfo is None:parsed = parsed.replace(tzinfo=timezone.utc)return parsed.astimezone(timezone.utc)

def escape_inline(value: str) -> str:return value.replace("\", "\\").replace("[", "\[").replace("]", "\]")

async def first_text(parent: Locator, selectors: tuple[str, ...]) -> str:for selector in selectors:locator = parent.locator(selector).firsttry:if await locator.count() and await locator.is_visible():value = clean_text(await locator.inner_text(timeout=2_000))if value:return valueexcept PlaywrightTimeoutError:passreturn ""

async def extract_post_url(card: Locator) -> str:selectors = ("a[href*='/feed/update/urn:li:activity:']","a[href*='/posts/']","a[href*='/pulse/']",)for selector in selectors:links = card.locator(selector)for index in range(min(await links.count(), 8)):href = await links.nth(index).get_attribute("href")if not href:continuehref = href.split("?", 1)[0]if href.startswith("/"):href = f"https://www.linkedin.com{href}"if href.startswith("https://www.linkedin.com/"):return hrefurn = await card.get_attribute("data-urn")if urn and urn.startswith("urn:li:activity:"):return f"https://www.linkedin.com/feed/update/{urn}/"return ""

async def extract_date(card: Locator) -> tuple[str, datetime | None]:time_element = card.locator("time[datetime]").firstif await time_element.count():raw = await time_element.get_attribute("datetime") or ""parsed = parse_datetime(raw)if parsed:return parsed.date().isoformat(), parsedvisible = await first_text(card, DATE_SELECTORS)return visible or "Unknown", None

async def find_post_cards(page: Page) -> Locator:for selector in POST_CARD_SELECTORS:cards = page.locator(selector)if await cards.count():return cardsreturn page.locator(POST_CARD_SELECTORS[0])

async def page_author_name(page: Page, profile_url: str) -> str:for selector in ("main h1", "h1.text-heading-xlarge", ".pv-text-details__left-panel h1"):locator = page.locator(selector).firsttry:if await locator.count():name = clean_text(await locator.inner_text(timeout=3_000))if name:return nameexcept PlaywrightTimeoutError:passreturn profile_url.rstrip("/").rsplit("/", 1)[-1].replace("-", " ").title()

async def ensure_logged_in(page: Page, headless: bool) -> None:await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")if "/login" not in page.url and "/checkpoint/" not in page.url:returnif headless:raise RuntimeError("Login is required. Run once without --headless, sign in in the browser, ""then rerun with --headless if desired.")LOG.warning("Sign in to LinkedIn in the browser window (waiting up to 5 minutes).")try:await page.wait_for_url(re.compile(r"https://www\.linkedin\.com/(feed/?(?:\?.*)?|in/.*)"),timeout=300_000,)except PlaywrightTimeoutError as exc:raise RuntimeError("Login was not completed within 5 minutes.") from exc

async def extract_posts(page: Page, fallback_author: str) -> list[Post]:cards = await find_post_cards(page)posts: list[Post] = []seen: set[str] = set()for index in range(await cards.count()):card = cards.nth(index)try:content = await first_text(card, CONTENT_SELECTORS)post_url = await extract_post_url(card)if not content or not post_url or post_url in seen:continueauthor = await first_text(card, AUTHOR_SELECTORS) or fallback_authorpost_date, published_at = await extract_date(card)except PlaywrightTimeoutError:LOG.debug("Timed out parsing post card %s", index)continueseen.add(post_url)posts.append(Post(author, post_date, post_url, content, published_at))return posts

async def collect_profile(page: Page,profile_url: str,max_scrolls: int,max_posts: int,cutoff: datetime,) -> tuple[str, list[Post]]:LOG.info("Opening %s", activity_url(profile_url))await page.goto(activity_url(profile_url), wait_until="domcontentloaded", timeout=60_000)if "/login" in page.url or "/checkpoint/" in page.url:raise RuntimeError("LinkedIn requested login or account verification.")try:await page.wait_for_selector(", ".join(POST_CARD_SELECTORS), state="attached", timeout=15_000)except PlaywrightTimeoutError:LOG.warning("No post cards appeared for %s", profile_url)

author = await page_author_name(page, profile_url)
previous_count = -1
stable_rounds = 0
for _ in range(max_scrolls):
    count = await (await find_post_cards(page)).count()
    if count >= max_posts:
        break
    stable_rounds = stable_rounds + 1 if count == previous_count else 0
    if stable_rounds >= 2:
        break
    previous_count = count
    await page.mouse.wheel(0, 2_500)
    await page.wait_for_timeout(1_500)

posts = await extract_posts(page, author)
posts = [post for post in posts if post.published_at is None or post.published_at >= cutoff]
return author, posts[:max_posts]

def render_markdown(author: str, profile_url: str, posts: list[Post], collected_at: datetime) -> str:lines = [f"# LinkedIn posts — {escape_inline(author)}","",f"- Profile: {profile_url}",f"- Collected: {collected_at.isoformat(timespec='seconds')}",f"- Posts: {len(posts)}","",]if not posts:lines.extend(["No matching posts were found. The profile may have no recent posts, ""restricted activity, or LinkedIn's page structure may have changed.","",])for index, post in enumerate(posts, 1):lines.extend([f"## Post {index}","",f"- Author: {escape_inline(post.author_name)}",f"- Date: {escape_inline(post.post_date)}",f"- URL: {post.post_url}","",post.content,"","---","",])return "\n".join(lines)

async def run(args: argparse.Namespace) -> int:profile_urls = load_profile_urls(args.profiles_file)args.output_dir.mkdir(parents=True, exist_ok=True)args.user_data_dir.mkdir(parents=True, exist_ok=True)cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)collected_at = datetime.now(timezone.utc)failures = 0

async with async_playwright() as playwright:
    context = await playwright.chromium.launch_persistent_context(
        str(args.user_data_dir.resolve()),
        headless=args.headless,
        slow_mo=args.slow_mo,
        viewport={"width": 1440, "height": 1000},
        locale="en-US",
    )
    context.set_default_timeout(10_000)
    page = context.pages[0] if context.pages else await context.new_page()
    try:
        await ensure_logged_in(page, args.headless)
        for profile_url in profile_urls:
            try:
                author, posts = await collect_profile(
                    page, profile_url, args.max_scrolls, args.max_posts, cutoff
                )
                output_path = args.output_dir / safe_filename(author, profile_url)
                output_path.write_text(
                    render_markdown(author, profile_url, posts, collected_at),
                    encoding="utf-8",
                )
                LOG.info("Saved %s post(s) to %s", len(posts), output_path)
            except Exception:
                failures += 1
                LOG.exception("Failed to collect %s", profile_url)
    finally:
        await context.close()
return 1 if failures else 0

def main() -> int:args = parse_args()logging.basicConfig(level=getattr(logging, args.log_level),format="%(asctime)s %(levelname)s %(message)s",)try:return asyncio.run(run(args))except (FileNotFoundError, ValueError, RuntimeError) as exc:LOG.error("%s", exc)return 2except KeyboardInterrupt:LOG.warning("Interrupted.")return 130

if name == "main":sys.exit(main())
