<div align="center">

[简体中文](./README.md) · **English**

# OpportunityHandbook · 机会手册

**A field guide for the choices that shape what you can do next.**

Study, research, work, promotion, a career change, a move abroad, or a fresh start: understand the routes before you commit to one.

[Read the handbook (Chinese)](https://sver0411.github.io/OpportunityHandbook/) · [Browse by situation (Chinese)](https://sver0411.github.io/OpportunityHandbook/#/browse) · [Meet OpportunityRadar](https://github.com/Sver0411/OpportunityRadar/blob/main/README.en.md)

</div>

> The handbook and its online reader are currently written in Simplified Chinese. This page is an original English introduction to the project, not an English edition of every chapter.

## The question before “Which opportunity should I take?”

It is hard to compare options you do not know exist. A student may think the only choice is graduate school or a job, without knowing about research assistantships, industry projects, or a year spent building a portfolio. Someone already working may see “stay or quit” where there are quieter ways to test a new field.

OpportunityHandbook (机会手册) helps readers put names to those possibilities and examine them. It brings together routes that are usually explained in separate places: university offices, hiring pages, professional communities, official programmes, and other people's stories. The aim is to make the next decision clearer while leaving it in the reader's hands.

Its starting point is simple: an attractive label tells you very little. What matters is what an option requires, what it costs, what you can carry away from it, and what it makes possible afterward.

## Who it is for

The book begins with choices made in school, but it follows the questions that appear long after graduation.

| If you are… | Questions the handbook helps you work through |
| --- | --- |
| **Still studying** | Which course, project, internship, competition, or research experience deserves your limited time? Is further study worth it? |
| **Entering work** | How should you compare a first job, two offers, pay, team quality, and room to learn? |
| **Building a career** | What evidence of your work will travel with you? When is a move, promotion, or management track worth pursuing? |
| **Changing direction** | Which skills and relationships can cross into a new field, and which gaps need a deliberate bridge? |
| **Considering another country** | How do qualifications, language, cost, visas, and local rules affect an otherwise appealing route? |
| **Starting again** | What changes when you return to study or work, freelance, or try to build something of your own? |
| **Unsure what you want** | Which small experiments can teach you something before a large, expensive commitment? |

Many examples come from Chinese education and employment systems. Treat country-specific rules as local information to verify, not as universal advice.

## A way to compare unlike choices

The handbook does not score a job, degree, and research project as if they were interchangeable products. It gives you a common set of questions to bring to each one:

1. **What must be true before I can do it?** Check formal requirements such as qualifications, location, language, timing, and eligibility.
2. **What will it cost me?** Count time, money, lost income, attention, relocation, and the best alternative you would set aside.
3. **What will remain afterward?** Look for skills, work you can show, credentials, income, trusted relationships, and clearer knowledge of yourself.
4. **What will it open or close?** Some choices are easy to reverse; others narrow the next few years. Make that trade-off visible.

Imagine choosing between an internal promotion and returning to school. The title of either option cannot settle the question. The promotion might give you responsibility and proof that you can lead; the degree might be the entry requirement for the work you actually want. The useful comparison is between their real requirements, costs, and future options in your circumstances.

## Start with the problem in front of you

You do not need to read the book from beginning to end. These entry points lead to the Chinese text:

| Your question | Start here |
| --- | --- |
| “How do I know whether this is worth doing?” | [A framework for judging a choice](https://sver0411.github.io/OpportunityHandbook/pages/judge-worth-it/) |
| “How do I compare two very different options?” | [Compare them on the same terms](https://sver0411.github.io/OpportunityHandbook/pages/judge-compare-two-opportunities/) |
| “Which job offer should I accept?” | [Compare offers beyond the headline salary](https://sver0411.github.io/OpportunityHandbook/pages/offer-comparison/) |
| “Should I move into another field?” | [Questions to settle before a career change](https://sver0411.github.io/OpportunityHandbook/pages/switch-before-decide/) |
| “What is worth building over several years?” | [The things you can take with you](https://sver0411.github.io/OpportunityHandbook/pages/judge-long-term-accumulation/) |

The [online reader](https://sver0411.github.io/OpportunityHandbook/) also lets you browse by life stage, direction, effort, expected outcome, and evidence type. Alongside the main chapters, the repository includes [timelines](docs/timelines/), [decision tools](docs/tools/), and [focused guides](docs/manuals/) on research, competitions, open source, funding, and more.

## Two projects, two moments in the same decision

The handbook has a companion: [OpportunityRadar (机会雷达)](https://github.com/Sver0411/OpportunityRadar), an Agent Skill for finding and checking live opportunities.

| | OpportunityHandbook · 机会手册 | OpportunityRadar · 机会雷达 |
| --- | --- | --- |
| **Use it to ask** | What paths exist, and how should I judge them? | What is open now, and which leads fit my situation? |
| **Information** | Relatively durable explanations and decision methods | Current listings, official requirements, deadlines, and application routes |
| **What you leave with** | A clearer goal and a way to compare options | A checked shortlist and a practical next action |

For example, you might use the handbook to decide whether research is a meaningful experiment for you and what you hope to learn from it. Then ask OpportunityRadar to look for research projects, assistant roles, or relevant open-source work that is still available. The live search works better once you know what you are trying to test.

## How the information is maintained

An official rule, a research finding, an industry statistic, and someone's personal experience should not be presented with the same certainty. Entries distinguish these kinds of evidence, show when changeable information was last checked, and point readers back to sources. If a deadline, visa rule, or admission requirement matters to your decision, confirm it again with the responsible organisation.

The handbook does not promise an outcome, recommend paid programmes for commission, or replace professional advice on legal, medical, financial, or immigration matters. Its job is to make the reasoning and the remaining uncertainty visible.

The content is written in Markdown and published as a static site. If you find an outdated rule, a broken official link, an overconfident claim, or a missing route, [open an issue](https://github.com/Sver0411/OpportunityHandbook/issues) or read the [contribution guide](CONTRIBUTING.md).

<details>
<summary><strong>Repository and local preview</strong></summary>

<br>

| Path | What is there |
| --- | --- |
| [`book/`](book/) | The main chapters, organised around life and career decisions |
| [`docs/`](docs/) | Timelines, worksheets, countries, industries, and focused guides |
| [`meta/`](meta/) | Navigation, metadata, writing standards, and source rules |
| [`site/`](site/) | The static online reader |
| [`tools/`](tools/) | Build, validation, and content-audit scripts |

```bash
python3 tools/build.py
python3 -m http.server 8000 --directory site
```

To run the same release checks used for publication:

```bash
python3 tools/validate_release.py
```

</details>

## Reuse and attribution

The handbook text, including this English introduction, is available under [CC BY 4.0](LICENSE-CONTENT). You may share, adapt, and translate it, including for commercial use, with attribution. The site and tooling are available under the [MIT licence](LICENSE).

---

<div align="center">

**[Understand the route with 机会手册](https://sver0411.github.io/OpportunityHandbook/) · [Find a live opening with 机会雷达](https://github.com/Sver0411/OpportunityRadar)**

</div>
