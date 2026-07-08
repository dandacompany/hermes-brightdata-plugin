import pytest
from brightdata_plugin import datasets


def test_resolve_known_platform():
    assert datasets.resolve("amazon_product") == "gd_l7q7dkf244hwjntr0"


def test_resolve_linkedin_person():
    assert datasets.resolve("linkedin_person") == "gd_l1viktl72bvl7bjuj0"


def test_resolve_is_case_insensitive():
    assert datasets.resolve("AMAZON_PRODUCT") == "gd_l7q7dkf244hwjntr0"


def test_resolve_unknown_raises_with_available():
    with pytest.raises(datasets.UnknownPlatform) as exc:
        datasets.resolve("nonexistent")
    assert "amazon_product" in exc.value.available


def test_platforms_sorted_nonempty():
    p = datasets.platforms()
    assert p == sorted(p)
    assert len(p) >= 3


def test_expanded_platforms_registered():
    # v0.2.0 expansion — a sample of the verified collect-by-url dataset_ids
    assert datasets.resolve("linkedin_company") == "gd_l1vikfnt1wgvvqz95w"
    assert datasets.resolve("tiktok_posts") == "gd_lu702nij2f790tmv9h"
    assert datasets.resolve("x_posts") == "gd_lwxkxvnf1cynvib9co"
    assert len(datasets.platforms()) >= 20
