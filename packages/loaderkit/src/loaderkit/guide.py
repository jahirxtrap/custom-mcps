"""Embedded strategy for decompiling Minecraft and loader APIs with the minecraft-dev MCP."""
from __future__ import annotations

_OVERVIEW = """# Decompile & API reference strategy (multiloader)

modkit covers the mechanical workspace half; for the actual Minecraft / loader API use the
minecraft-dev MCP (package @mcdxai/minecraft-dev-mcp) and mcmodding-mcp. Never rely on training
data: Minecraft changes a lot between versions.

Priority for any API question:
1. mcmodding-mcp first (Fabric / NeoForge docs, events, convention tags).
2. Decompiled loader source via minecraft-dev (search_mod_code) when mcmodding-mcp lacks it.
3. External doc links last.

Mapping: always mojmap (unobfuscated on 26.1+, and the preferred choice on older versions too).

Loader decompile naming convention (do NOT invent 'forge-api' / 'fabric-api'):
- modId = fabric | forge | neoforge
- modVersion = the MC version (e.g. "1.21.1", "26.1.2")
One decompile per loader/version holds MC patched + that loader's API together, cached under
decompiled-mods/<loader>/<mcversion>/mojmap/."""

_VANILLA = """## Vanilla Minecraft
- decompile_minecraft_version(version, mapping="mojmap") once, then get_minecraft_source and
  search_minecraft_code to read classes, methods, fields and content.
- compare_versions / compare_versions_detailed to diff two versions during a migration.
- Vanilla is independent of the loaders; the Fabric merge below does NOT need vanilla in it."""

_FABRIC = """## Fabric (uber-jar merge required, every version)
Fabric API ships as an uber-jar with 40+ nested module jars in META-INF/jars/; split and repackage.
Source uber-jar:
  ~/.gradle/caches/modules-2/files-2.1/net.fabricmc.fabric-api/fabric-api/<api>/<hash>/fabric-api-<api>.jar
  jar xf <uber> META-INF/jars/
  mkdir merged && for j in META-INF/jars/*.jar; do (cd merged && jar xf "../$j"); done
  (cd merged && jar cf /tmp/fabric-api-<mc>-merged.jar .)
  decompile_mod_jar(jarPath="/tmp/fabric-api-<mc>-merged.jar", mapping="mojmap",
                    modId="fabric", modVersion="<mc>")"""

_FORGE = """## Forge
26.1+: single jar, decompile directly (already MC patched + Forge API):
  <project>/.gradle/mavenizer/repo/net/minecraftforge/forge/<forge>/forge-<forge>.jar
  decompile_mod_jar(jarPath=<that>, mapping="mojmap", modId="forge", modVersion="<mc>")

pre-26.1 (1.20.1 / 1.21.1 / 1.21.11): MUST merge. binpatched.jar has only net.minecraft.* and
com.mojang.*; the net.minecraftforge.* hooks/events live ONLY in universal[-srg].jar. Use both.
  MC patched: ~/.gradle/caches/forge_gradle/minecraft_user_repo/.../forge-<forge>-binpatched.jar
  Forge API : ~/.gradle/caches/forge_gradle/maven_downloader/.../forge-<forge>-universal-srg.jar (1.21.1+)
              ~/.gradle/caches/forge_gradle/maven_downloader/.../forge-<forge>-universal.jar (1.20.1)
  Merge both into one jar (jar xf each into merged/, then jar cf), then
  decompile_mod_jar(... modId="forge", modVersion="<mc>")."""

_NEOFORGE = """## NeoForge (TWO steps: the patched-merged jar has NO net.neoforged API)
The patched-merged jar contains ONLY patched Minecraft; the NeoForge API (events, payloads, FML,
registries, capabilities) is NOT in it. Do both:
1. decompile_mod_jar(modId="neoforge", modVersion="<mc>", mapping="mojmap", jarPath=
   "<project>/neoforge/build/moddev/artifacts/minecraft-patched-<neoforge>-merged.jar") -> patched MC.
2. Add the NeoForge API from its PURE sources jar (javadoc + param names, better than the universal):
   ~/.gradle/caches/modules-2/files-2.1/net.neoforged/neoforge/<neoforge>/<hash>/neoforge-<neoforge>-sources.jar
   DEST=~/AppData/Roaming/minecraft-dev-mcp/decompiled-mods/neoforge/<mc>/mojmap
   (cd "$DEST" && jar xf "<sources.jar>" net/neoforged)   it is 100% net.neoforged, won't clobber MC
3. index_mod(modId="neoforge", modVersion="<mc>", mapping="mojmap", force=true) to rebuild the index.
4. Verify: search_mod_code for "PayloadRegistrar|RegisterPayloadHandlersEvent" must return hits."""

_MIGRATION = """## Version migration references
- NeoForge primers (Java/API breaks), per target version:
  https://github.com/ChampionAsh5357/neoforged-github/blob/update/<v>/primers/<v>/index.md
- misode changelog (data/pack/registry/component changes; check on EVERY bump, incl. minor & snapshots):
  https://misode.github.io/versions/?id=<v>&tab=changelog
- mcasset.cloud (vanilla assets; copy Mojang phrasing per locale for translation):
  https://mcasset.cloud/<v>/assets/minecraft/lang/<locale>.json
- analyze_mixin validates mixins against the target MC; validate_access_widener checks .aw files."""

_SECTIONS = {
    "overview": _OVERVIEW,
    "vanilla": _VANILLA,
    "fabric": _FABRIC,
    "forge": _FORGE,
    "neoforge": _NEOFORGE,
    "migration": _MIGRATION,
}


def decompile_topics() -> list[str]:
    return list(_SECTIONS)


def decompile_guide(topic: str = "") -> str:
    key = topic.strip().lower()
    if not key:
        return "\n\n".join(_SECTIONS[name] for name in _SECTIONS)
    if key in _SECTIONS:
        return _SECTIONS[key]
    return f"Unknown topic '{topic}'. Available: {', '.join(_SECTIONS)}"
