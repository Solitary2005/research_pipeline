---
arxiv_id: "manual-20260730-transformer-transformer-a-unified-model"
title: "Transformer Transformer: A Unified Model for Motion-Conditioned Robot Co-design"
authors: "Huy Ha, Karen Liu, Shuran Song"
published_date: 2027-07-28
primary_category: ""
topic: "control"
has_summary: true
has_podcast: true
interesting: true
permalink: /papers/manual-20260730-transformer-transformer-a-unified-model/
---

## Abstract

An often overlooked factor of robot manipulation performance is the embodiment of the robot itself. Motivated by this problem, we study motionconditioned robot co-design, where the goal is to generate complete robot designs that track target end-effector trajectories (from human demonstrations) while optimizing user-defined rewards. We introduce Transformer Transformer, a diffusion

transformer trained on RoboTokens, a unified tokenization of robot embodiments,

states, and actions. The same architecture can be used across embodiment spaces

(e.g., wheeled bimanual, quadrupeds, humanoids) and use cases (embodiment

generation, cross embodiment controller). Rather than overfitting to one reward

function, Transformer Transformer is a dynamics model, whose reward-agnostic

state and action predictions can be converted into reward-specific value predictions. These value predictions are used to steer embodiment diffusion towards

high value robot designs, through a procedure we call Dynamics Self-Guidance.

Experiments across multiple design spaces show zero-shot optimization of unseen rewards and trajectories, improving performance and runtime over the evolutionary baseline. Finally, we fabricated an optimized ALOHA design, which

reduced tracking error by over 70% compared to the original design. Check out

transformer-transformer.github.io for summary/result videos.

## Links

- *Manually uploaded paper*

## Actions

<a class="btn-request" href="https://github.com/Solitary2005/research_pipeline/issues/new?template=summary-request.yml&title=[Summary]+manual-20260730-transformer-transformer-a-unified-model&arxiv_id=manual-20260730-transformer-transformer-a-unified-model&paper_title=Transformer%20Transformer%3A%20A%20Unified%20Model%20for%20Motion-Conditioned%20Robot%20Co-design" target="_blank">Request Summary + Podcast</a>

---

<audio controls style="width:100%">
  <source src="/research_pipeline/assets/audio/manual-20260730-transformer-transformer-a-unified-model.mp3" type="audio/mpeg">
  Your browser does not support audio.
</audio>

[View full summary + podcast page](/research_pipeline/podcasts/manual-20260730-transformer-transformer-a-unified-model/)
