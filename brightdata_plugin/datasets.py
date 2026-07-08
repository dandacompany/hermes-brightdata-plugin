from __future__ import annotations

# Only dataset_ids verified directly from official docs.brightdata.com
# collect-by-url scraper pages. Add new platforms only after confirming the
# dataset_id in the official docs (discover-by-keyword scrapers are excluded —
# this plugin's web_data tool is URL-input only).
DATASET_IDS: dict[str, str] = {
    # Amazon
    "amazon_product": "gd_l7q7dkf244hwjntr0",
    "amazon_product_reviews": "gd_le8e811kzy4ggddlq",
    "amazon_product_search": "gd_lwdb4vjm1ehb499uxs",
    "amazon_seller_info": "gd_lhotzucw1etoe5iw1k",
    # LinkedIn
    "linkedin_person": "gd_l1viktl72bvl7bjuj0",
    "linkedin_company": "gd_l1vikfnt1wgvvqz95w",
    "linkedin_job_listings": "gd_lpfll7v5hcqtkxl6l",
    "linkedin_posts": "gd_lyy3tktm25m4avu764",
    # Instagram
    "instagram_profile": "gd_l1vikfch901nx3by4",
    "instagram_posts": "gd_lk5ns7kz21pck8jpis",
    "instagram_reels": "gd_lyclm20il4r5helnj",
    "instagram_comments": "gd_ltppn085pokosxh13",
    # TikTok
    "tiktok_profiles": "gd_l1villgoiiidt09ci",
    "tiktok_posts": "gd_lu702nij2f790tmv9h",
    "tiktok_comments": "gd_lkf2st302ap89utw5k",
    # Facebook
    "facebook_posts": "gd_lyclm1571iy3mv57zw",
    "facebook_profiles": "gd_mf0urb782734ik94dz",
    # YouTube
    "youtube_videos": "gd_lk56epmy2i5g7lzu0k",
    "youtube_profiles": "gd_lk538t2k2p1k3oos71",
    "youtube_comments": "gd_lk9q0ew71spt1mxywf",
    # X (Twitter)
    "x_posts": "gd_lwxkxvnf1cynvib9co",
    "x_profile_posts": "gd_lwxmeb2u1cniijd7t4",
    # Business
    "crunchbase_company": "gd_l1vijqt9jfj7olije",
}


class UnknownPlatform(ValueError):
    def __init__(self, platform: str, available: list[str]):
        super().__init__(f"Unknown platform '{platform}'. Available: {available}")
        self.platform = platform
        self.available = available


def resolve(platform: str) -> str:
    key = platform.strip().lower()
    if key not in DATASET_IDS:
        raise UnknownPlatform(platform, platforms())
    return DATASET_IDS[key]


def platforms() -> list[str]:
    return sorted(DATASET_IDS)
