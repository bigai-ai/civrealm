# *CivRealm*: A Learning and Reasoning Odyssey in *Civilization* for Decision-Making Agents

![Punic War](assets/punic_war_base.jpg)

CivRealm is an interactive environment for the open-source strategy game [Freeciv-web](https://github.com/freeciv/freeciv-web) based on [Freeciv](https://www.freeciv.org/), a Civilization-inspired game. Within CivRealm, we provide interfaces for two typical agent types: tensor-based reinforcement learning agents based on the [Gymnasium](https://gymnasium.farama.org/) API, and language-based agents powered by language models.

<title>Example</title>
<style>
.grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  grid-gap: 20px;
  align-items: center;
  }
.grid > article {
  border: 1px solid #ccc;
  box-shadow: 2px 2px 6px 0px  rgba(0,0,0,0.3);
}
.grid > article img {
  max-width: 100%;
}
.text {
  padding: 0 20px 20px;
}
.text > button {
  background: #ccc;<!--#DF9295-->
  border: 0;
  color: white;
  padding: 10px;
  width: 100%;
  }
</style>
<main class="grid">
  <article>
    <div class="text">
      <h3>Getting Started</h3>
      <p>New to Civrealm? Start with our Beginner's Guide. This guide offers an overview of CivRealm's core concepts and provides links to further tutorials.</p>
      <button><a href="getting_started/requirements.html">To the beginner</a></button>
    </div>
  </article>
  <article>
    <div class="text">
      <h3>Advanced Materials</h3>
      <p>The advanced materials offer comprehensive insights into Civrealm's essential concepts, complemented by valuable background details.</p>
      <button><a href="advanced_materials/game_settings.html">To the old hand</a></button>
    </div>
  </article>
  <article>
    <div class="text">
      <h3>API Reference</h3>
      <p>The reference guide provides an in-depth explanation of the functions and objects incorporated within Civrealm. It elaborates on the function APIs.</p>
      <button><a href="api_reference/environments.html">To the reference</a></button>
    </div>
  </article>
  <article>
    <div class="text">
      <h3>Releases</h3>
      <p>The official versions of CivRealm, along with their associated dependencies and downstream repositories.</p>
      <button><a href="releases/releases.html">Align your version</a></button>
    </div>
  </article>
  <article>
    <div class="text">
      <h3>Contribute</h3>
      <p>How to Contribute to CivRealm: This guide will help you create or customize the environment. </p>
      <button><a href="notes/contribute.html">Contribute to CivRealm</a></button>
    </div>
  </article>
  <article>
    <div class="text">
      <h3>FAQ & Resources</h3>
      <p style="white-space: pre-line">If you have any further questions, the FAQ page and resources may assist you.

      </p>
      <button><a href="misc/faq.html">Find your answer</a></button>
    </div>
  </article>
</main>

We also provide a set of tools for training and evaluating agents, as well as a set of baselines for both agent types. We hope that CivRealm can serve as a testbed for developing and evaluating agents that can learn and reason in complex environments.
