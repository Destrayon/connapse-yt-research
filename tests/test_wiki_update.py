from connapse_yt.manifest import Manifest, ManifestEntry
from connapse_yt.wiki_update import plan_update, Operation


def test_plan_update_existing_topic_produces_four_ops():
    m = Manifest(entries=[
        ManifestEntry(
            topic="hooks/p1/cold-open",
            current_version=2,
            current_path="wiki/hooks/p1/cold-open.v2.md",
        ),
    ])
    ops = plan_update(
        manifest=m,
        topic="hooks/p1/cold-open",
        new_body="# v3\n\nUpdated body.\n",
        new_frontmatter={"type": "evergreen", "version": 3},
    )
    kinds = [op.kind for op in ops]
    # upload new, delete old, archive old (upload to /archive/), update manifest
    assert kinds == ["upload", "delete", "upload", "upload_manifest"]

    upload_new = ops[0]
    assert upload_new.path == "wiki/hooks/p1/cold-open.v3.md"
    assert "# v3" in upload_new.content

    delete_old = ops[1]
    assert delete_old.path == "wiki/hooks/p1/cold-open.v2.md"

    archive = ops[2]
    assert archive.path == "archive/wiki/hooks/p1/cold-open.v2.md"


def test_plan_update_new_topic_has_no_delete():
    m = Manifest(entries=[])
    ops = plan_update(
        manifest=m,
        topic="hooks/p2/token-cost",
        new_body="# v1\n",
        new_frontmatter={"type": "evergreen", "version": 1},
    )
    kinds = [op.kind for op in ops]
    assert "delete" not in kinds
    # new uploads new version + manifest, no archive step
    assert kinds == ["upload", "upload_manifest"]
