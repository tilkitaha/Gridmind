# Thesis review against the FEM seminar rules

14 October 2026. `defense/GridMind_Thesis_Development.docx` checked against `.claude/skills/fem-thesis-rules/SKILL.md` (diploma seminar rules). Formatting was read from the document's styles and section settings; content items were checked by locating the relevant chapters. Nothing in the thesis was changed. The faculty template and regulations take precedence over this review.

## Summary

Formatting is compliant. The gaps are in the order of the front matter, the title, explicit object/subject/objective statements, the closing chapter's intellectual-property analysis, and the variety of literature.

## Met

| Rule | Finding |
| --- | --- |
| Margins inner 3.5, outer 2.5, top and bottom 2.5 cm | 3.5 / 2.5 / 2.5 / 2.5 cm with mirrored margins |
| Font and sizes | Times New Roman; body 12 pt, section titles 14 pt, subsections 12 pt |
| Line spacing 1.5, no paragraph spacing | 1.5, 0 pt before and after |
| Alignment and hyphenation | Justified; automatic hyphenation on |
| Page numbers | PAGE field bottom right; none on the title page |
| Volume of at least 120,000 characters | About 149,400 characters of body text plus 9,100 in tables |
| Abstracts | Polish (Streszczenie) and English present |
| Back matter order | References → List of tables → List of figures → List of appendices → Appendices A, B |
| Chapter structure | Introduction (1); literature (2); problem and methodology (3–4); results (5–7); solution, implementation and conclusions (8–9) |
| Tables | All 24 have a numbered caption above and a "Source:" line below |
| Implementation possibility | Chapter 8 covers users, economics, pilot conditions and handover |
| Citation style | Author-date; references alphabetical (two ENTSO-E entries share an author and differ only in date order) |

## Not met or incomplete

| # | Rule | Finding | Suggested action |
| --- | --- | --- | --- |
| 1 | Abstracts precede the table of contents | Contents comes first, then Streszczenie and Abstract | Move Contents after both abstracts |
| 2 | Title uses an engineering form and matches the evidence | "AI and Blockchain Integration in Smart Grids for Autonomous Energy Trading and Risk Optimization" uses none of the recommended forms and names autonomous trading and risk optimisation, which the thesis reports as unfinished | Team and supervisor decide; the title must match USOS APD. An evidence-matched direction is "Comparison of …" or "Design of …" for community battery control and settlement |
| 3 | Object, subject and objective stated explicitly | None of the three is named | Add a short subsection in 1.1 with the three statements |
| 4 | SMART goal | The goal has no measurable target or time frame | State the endpoint, data period and comparison |
| 5 | Introduction: justification of the subject choice and the structure of the work | The introduction (about 4,200 characters) has no explicit justification and only refers to Chapters 5–8 in passing | Add a motivation paragraph and a chapter-by-chapter outline |
| 6 | Mandatory justification of methods and tools | Methods are described; explicit reasons for choosing IPPO/MAPPO, MPC, Ridge, the block bootstrap and the signed ledger over alternatives are not collected in one place | Add a justification table in Chapter 4 |
| 7 | Summary: intellectual property analysis | Chapters 8–9 say only that the work is not a claim of patentable novelty; no software licence (MIT), data licence (CC0), ownership or university publication priority | Add an IP subsection: code licence, data licence, authorship, university priority, patentability |
| 8 | Summary: level of achievement per objective | 9.1 summarises results but does not mark each objective as met, partly met or not met | Add a table per research question or objective |
| 9 | Literature types: books, periodicals, papers, standards | 22 references, mostly papers and web documentation; no books and no standards | Add sources actually used. The ENTSO-E data format follows IEC 62325, and standard texts on reinforcement learning, MPC and forecasting are natural candidates |
| 10 | Every figure has a source line | Figure 6.2 has none; Figures 5.1, 5.2 and 6.1 have it | Add "Source: own study" or the data source |

## Not verifiable from the file

- Whether the title page matches the current faculty template exactly.
- Whether the title matches the APD entry.
- Whether a separate list of symbols is expected in addition to "Abbreviations and notation".
