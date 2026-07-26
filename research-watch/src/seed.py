"""Seed registry.json with the nine foundational sources and the standards.

Run once: python -m src.seed
Existing records are preserved; seeding only adds ids that are missing.
"""
from __future__ import annotations
from .common import DATA, registry, save_json, today

FOUNDATIONS = [
    dict(id="sails-2026",
         title="Scenario-Based AI Literacy Scale (SAILS)",
         authors="Scheibenzuber et al.",
         venue="British Journal of Educational Technology",
         year=2026,
         url="https://doi.org/10.1111/bjet.70065",
         doi="10.1111/bjet.70065",
         type="foundational",
         applies_to=dict(curriculum=dict(refs=["toolkit-diagnostic", "toolkit-report", "W1-S1"], note="")),
         summary="A validated instrument that measures AI literacy through eight anchored scenarios across two subscales, critical-reflective and instrumental.",
         why_it_matters="It is the basis of the literacy diagnostic and the reason upskilling can be measured before and after delivery instead of surveyed."),
    dict(id="tir-2026",
         title="Interrogative Reasoning and the Problem with the Human in the Loop",
         authors="Styles, Williams, Teran, and Johnson",
         venue="Just Tech, Social Science Research Council",
         year=2026,
         url="https://just-tech.ssrc.org/articles/interrogative-reasoning-and-the-problem-with-the-human-in-the-loop/",
         doi="",
         type="foundational",
         applies_to=dict(curriculum=dict(refs=["W2-S2", "W3-S1", "toolkit-sorting"], note="")),
         summary="Reframes ethical AI as a question of power, belief, and timing, and shows why a single human reviewer fails to catch the harms a community would see.",
         why_it_matters="It is the basis for moving from human in the loop to communities in the loop, and it is credited to Measure, the curriculum's partner."),
    dict(id="care-model",
         title="CARE Model and Communities in the Loop",
         authors="Measure",
         venue="Measure",
         year=2026,
         url="https://communityintheloop.org/",
         doi="",
         type="foundational",
         applies_to=dict(curriculum=dict(refs=["W1-S2", "W3-S1", "toolkit-rubric"], note="")),
         summary="A practice model treating community accountability as a structural element of governance design.",
         why_it_matters="It supplies the community anchor exercise and the community impact category scored in the tool evaluation rubric."),
    dict(id="nist-airmf",
         title="AI Risk Management Framework",
         authors="National Institute of Standards and Technology",
         venue="NIST",
         year=2023,
         url="https://www.nist.gov/itl/ai-risk-management-framework",
         doi="",
         type="standard",
         applies_to=dict(curriculum=dict(refs=["W2-S2", "toolkit-charter"], note="")),
         summary="A voluntary risk management framework covering govern, map, measure, and manage functions. Version 1.0 is under revision.",
         why_it_matters="Texas TRAIGA names it as the safe harbor standard, which makes it the reference point for organizations operating in Texas."),
    dict(id="iso-42001",
         title="ISO/IEC 42001, AI management systems",
         authors="ISO and IEC",
         venue="ISO",
         year=2023,
         url="https://www.iso.org/standard/42001",
         doi="",
         type="standard",
         applies_to=dict(curriculum=dict(refs=["W2-S2", "toolkit-charter"], note="")),
         summary="The first management system standard for artificial intelligence, covering the structures an organization puts around AI use.",
         why_it_matters="It gives the governance architecture options a recognised external reference an auditor or funder will know."),
    dict(id="australia-principles",
         title="Australia's 8 AI Ethics Principles",
         authors="Department of Industry, Science and Resources",
         venue="Australian Government",
         year=2019,
         url="https://www.industry.gov.au/publications/australias-artificial-intelligence-ethics-principles",
         doi="",
         type="foundational",
         applies_to=dict(curriculum=dict(refs=["W1-S2", "W3-S1", "toolkit-sorting"], note="")),
         summary="Eight plain-language principles covering wellbeing, human-centred values, fairness, privacy, reliability, transparency, contestability, and accountability.",
         why_it_matters="Its plain language makes it the scaffold participants use when sorting scenarios, without needing a legal background."),
    dict(id="fedorich-stack",
         title="The AI Governance Stack: A Framework for the Next Three Years",
         authors="William Fedorich",
         venue="AI Governance for Leaders",
         year=2026,
         url="https://williamfedorich.substack.com/p/the-ai-governance-stack-a-framework",
         doi="",
         type="foundational",
         applies_to=dict(curriculum=dict(refs=["W2-S2", "toolkit-charter"], note="")),
         summary="A five-layer governance architecture covering policy, oversight, controls, audit, and disclosure.",
         why_it_matters="It is the structure behind the governance charter and the maturity assessment leadership commits to."),
    dict(id="anthropic-exponential",
         title="Policy on the AI Exponential, including the Advanced AI Framework",
         authors="Anthropic",
         venue="Anthropic",
         year=2026,
         url="https://www.anthropic.com/policy-on-the-ai-exponential",
         doi="",
         type="policy",
         applies_to=dict(curriculum=dict(refs=["W2-S1", "toolkit-charter"], note="")),
         summary="Two policy proposals. The Advanced AI Framework sets out four categories of catastrophic risk: biological, cyber, loss of control, and automated research and development.",
         why_it_matters="Its four risk categories are the taxonomy the governance charter uses, and it supplies the pace of change argument behind the why now framing."),
    dict(id="brookings-sb53",
         title="What is California's AI safety law?",
         authors="Alikhani and Kane",
         venue="Brookings Institution",
         year=2025,
         url="https://www.brookings.edu/articles/what-is-californias-ai-safety-law/",
         doi="",
         type="policy",
         applies_to=dict(curriculum=dict(refs=["W2-S1"], note="")),
         summary="An analysis of California SB 53, covering transparency duties and its whistleblower protections.",
         why_it_matters="SB 53 is the pattern for state-level AI regulation, and its whistleblower provisions are modelled directly in the governance charter."),
]

EXTRA = [
    dict(id="traiga",
         title="TRAIGA, Texas Responsible AI Governance Act, HB 149",
         authors="Texas Legislature",
         venue="State of Texas",
         year=2025,
         url="https://capitol.texas.gov/BillLookup/History.aspx?LegSess=89R&Bill=HB149",
         doi="",
         type="context",
         applies_to=dict(curriculum=dict(refs=["W2-S1"], note="")),
         summary="Texas legislation governing AI use, effective 1 January 2026, with NIST AI RMF as a safe harbor.",
         why_it_matters="It is the law that applies to organizations in the curriculum's home market, which makes governance a compliance matter as well as an ethical one."),
]


def main() -> None:
    existing = {r["id"]: r for r in registry()}
    added = []
    for rec in FOUNDATIONS + EXTRA:
        if rec["id"] in existing:
            continue
        rec = dict(rec)
        rec.setdefault("added", today())
        rec.setdefault("last_verified", today())
        rec.setdefault("status", "active")
        rec.setdefault("superseded_by", None)
        existing[rec["id"]] = rec
        added.append(rec["id"])
    ordered = sorted(existing.values(), key=lambda r: (r["type"] != "foundational", r["id"]))
    save_json(DATA / "registry.json", ordered)
    print(f"registry.json now holds {len(ordered)} records; added {len(added)}: {', '.join(added) or 'none'}")


if __name__ == "__main__":
    main()
