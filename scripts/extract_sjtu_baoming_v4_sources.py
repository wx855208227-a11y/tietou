from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

from extract_sjtu_baoming_v3_sources import extract


ROOT = Path(__file__).resolve().parents[1]
AGENT_DIR = ROOT.parent
WORK = AGENT_DIR / "work/sjtu_baoming_20260914_v4"
SOURCES = WORK / "sources"
TEXT = WORK / "text"
INVENTORY = WORK / "source_inventory.json"

INPUTS = {
    "general_rapid": AGENT_DIR
    / "inbox/feishu/om_x100b654e131134acc4f02cfcebe479e/27_.docx",
    "general_yibentong": AGENT_DIR
    / "inbox/feishu/om_x100b654e11c544a8de24a98fcbc2638/27_.docx",
    "clinical_rapid": AGENT_DIR
    / "inbox/feishu/om_x100b654e1310c4a0dee732125e4bdbc/_-_2025_.docx",
    "clinical_yibentong": AGENT_DIR
    / "inbox/feishu/om_x100b654e11c478a0deb98f76d88e58c/_-_2025_.docx",
    "experiment_rapid": AGENT_DIR
    / "inbox/feishu/om_x100b654eb81070a0c3dd1d469898152/_2027_9.10.docx",
    "experiment_yibentong": AGENT_DIR
    / "inbox/feishu/om_x100b654e11c7c8b4deb7fe941c3d5b5/_1_.docx",
}

OUTPUT_NAMES = {
    "general_rapid": "上交普通心理学速背手册.docx",
    "general_yibentong": "上交普通心理学一本通_本日新版.docx",
    "clinical_rapid": "上交临床心理学速背手册2025定稿.docx",
    "clinical_yibentong": "上交临床心理学一本通2025定稿.docx",
    "experiment_rapid": "上交实验心理学速背手册2027定稿9.10.docx",
    "experiment_yibentong": "上交实验心理学一本通.docx",
}

EXPECTED_HASHES = {
    "general_rapid": "799b8f8d2e350cb3de5e73f08049715f16cc8ec43be895aebb3ea36cce2bff17",
    "general_yibentong": "5f8f56751596654b92cf7710949bf2bd38d97d06d11b140adb33100202e45fa6",
    "clinical_rapid": "fa7ffd9b781870fd5a7a40824022dbf867be80cf8a68696f5461df6d77720395",
    "clinical_yibentong": "40ecb74a3a1b3ab2d0ffdfcd19411bafe4ce1f9498fb893ceb972f9f5e3ff383",
    "experiment_rapid": "e016004ec2001b41a2a51fa0935afa761ad8a04f160277882721df33dd0f8851",
    "experiment_yibentong": "5d0394e7dbe30484f99dd0275dd2c79fdac11cfae6368bcfcfcf8dda6ec01feb",
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> None:
    SOURCES.mkdir(parents=True, exist_ok=True)
    TEXT.mkdir(parents=True, exist_ok=True)
    inventory: dict[str, dict[str, object]] = {}
    for key, source in INPUTS.items():
        assert source.is_file(), source
        assert digest(source) == EXPECTED_HASHES[key], (key, digest(source))
        local = SOURCES / OUTPUT_NAMES[key]
        shutil.copy2(source, local)
        inventory[key] = extract(local, TEXT / f"{key}.md")
    INVENTORY.write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(inventory, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
