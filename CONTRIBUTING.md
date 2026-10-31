# Contributing to OBS-10

Thanks for helping. This is a draft design, and outside review is the point.

## Ways to help

| You are... | Best place |
|---|---|
| An engineer reviewing structure, anchors or connections | Issue: **Structural / engineering review** (PDF markups welcome as attachments) |
| An accessibility specialist or rider | Issue: **Accessibility** |
| Pricing or finding parts in your country | Issue: **Parts and sourcing** |
| Confused by a manual page | Issue: **Manual clarity** (quote the page and step number) |
| Adapting it for your climate, codes or fleet | Issue: **Local adaptation** |
| Someone who built a prototype | Issue: **Build report** (photos and time taken help most) |
| Just have an idea or question | [Discussions](../../discussions) |

## Ground rules

- Keep parts generic. Describe parts by profile, size and finish, never by brand or store, so the design works everywhere. Region-specific shopping lists belong in `bom/` as separate files named by country.
- Metric first, imperial second.
- No welding and no metal cutting in the core design. Proposals that break this rule are welcome, but label them as variants.
- Engineering claims need a basis. Cite the code, test data or calculation.

## Changing files

- **Manual pages** are standalone HTML in `manual/pages/`. Run `python tools/build_pdfs.py --png` to rebuild the PDF and previews.
- **Drawings** are HTML/SVG in `drawings/src/`. Rebuild the same way.
- **Illustrations** come from `src/ikea_steps.py`. Change dimensions in `src/ikea.py`, not by editing images.
- Open a pull request that describes what changed and why, and add a line to `CHANGELOG.md`.

## Revisions

Released revisions (Rev A, Rev B, and so on) are tagged so agencies can cite exactly what they reviewed. Only a revision that carries an engineer's stamp in its release notes is suitable for construction, and only in that engineer's jurisdiction.
