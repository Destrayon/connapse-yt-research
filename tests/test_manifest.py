from connapse_yt.manifest import Manifest, ManifestEntry


def test_manifest_round_trips():
    m = Manifest(
        entries=[
            ManifestEntry(topic="hooks/p1-persistent-memory/cold-open-patterns",
                          current_version=3, current_path="wiki/hooks/p1-persistent-memory/cold-open-patterns.v3.md"),
            ManifestEntry(topic="strategy/positioning-theses",
                          current_version=5, current_path="wiki/strategy/positioning-theses.v5.md"),
        ]
    )
    rendered = m.to_markdown()
    parsed = Manifest.from_markdown(rendered)
    assert parsed == m


def test_manifest_bump_version():
    m = Manifest(entries=[
        ManifestEntry(topic="hooks/p1/cold-open",
                      current_version=2,
                      current_path="wiki/hooks/p1/cold-open.v2.md"),
    ])
    new_path = m.bump("hooks/p1/cold-open")
    assert new_path == "wiki/hooks/p1/cold-open.v3.md"
    assert m.entries[0].current_version == 3
    assert m.entries[0].current_path == "wiki/hooks/p1/cold-open.v3.md"


def test_manifest_add_new_topic_if_missing():
    m = Manifest(entries=[])
    path = m.bump("hooks/p1/new-pattern")
    assert path == "wiki/hooks/p1/new-pattern.v1.md"
    assert len(m.entries) == 1
    assert m.entries[0].current_version == 1
