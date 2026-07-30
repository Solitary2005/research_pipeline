---
layout: podcast
arxiv_id: "manual-20260730-transformer-transformer-a-unified-model"
title: "Transformer Transformer: A Unified Model for Motion-Conditioned Robot Co-design"
authors: "Huy Ha, Karen Liu, Shuran Song"
published_date: 2027-07-28
permalink: /podcasts/manual-20260730-transformer-transformer-a-unified-model/
---

<audio controls style="width:100%;margin-bottom:2em;">
  <source src="/research_pipeline/assets/audio/manual-20260730-transformer-transformer-a-unified-model.mp3" type="audio/mpeg">
  Your browser does not support audio.
</audio>

## Paper

**Transformer Transformer: A Unified Model for Motion-Conditioned Robot Co-design** — Huy Ha, Karen Liu, Shuran Song

## Summary Card

### Motivation
Robot manipulation performance is often limited by the robot's embodiment, which is frequently overlooked in policy learning. Given embodiment-agnostic task representations like end-effector trajectories, the ability to automatically generate optimized robot designs that can track these trajectories is crucial for improving task success and transfer across robots.

### Method
The paper introduces Transformer Transformer, a diffusion transformer trained on RoboTokens, a unified tokenization of robot embodiments, states, and actions. The key innovation is Dynamics Self-Guidance, which converts the model's reward-agnostic dynamics predictions into reward-specific value predictions to steer embodiment diffusion towards high-value designs, enabling zero-shot optimization of unseen rewards and trajectories without additional training.

### Key Results
Across fixed-base, quadruped, and bimanual mobile manipulator design spaces, Transformer Transformer achieves zero-shot optimization of user-specified rewards and trajectories, outperforming evolutionary baselines in both performance and runtime. Fabrication of an optimized ALOHA design reduced tracking error by over 70% (73% for cloth unfolding) and maximum joint velocity by 30% compared to the original design.

### Takeaways
This work demonstrates that a single generative model can unify embodiment generation, cross-embodiment control, and reward optimization, simplifying the robot co-design pipeline. By treating dynamics as a reward-agnostic prior, it enables flexible adaptation to diverse tasks and rewards, suggesting a paradigm shift towards foundation models for robot design and control.

[Back to paper page](/research_pipeline/papers/manual-20260730-transformer-transformer-a-unified-model/)
