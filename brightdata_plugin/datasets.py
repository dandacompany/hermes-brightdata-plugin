from __future__ import annotations

# 공식 문서 curl 예시에서 직접 확인된 dataset_id만 등록.
# 추가 platform은 docs.brightdata.com에서 dataset_id 확인 후 등재할 것.
DATASET_IDS: dict[str, str] = {
    "amazon_product": "gd_l7q7dkf244hwjntr0",
    "linkedin_person": "gd_l1viktl72bvl7bjuj0",
    "instagram_profile": "gd_l1vikfch901nx3by4",
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
