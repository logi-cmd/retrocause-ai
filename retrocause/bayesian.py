"""NumPyro贝叶斯路径概率推断"""

from __future__ import annotations
from typing import Any


def _load_jax():
    import jax
    import jax.numpy as jnp

    return jax, jnp


def _load_numpyro():
    import numpyro
    import numpyro.distributions as dist
    from numpyro.infer import MCMC, NUTS

    return numpyro, dist, MCMC, NUTS


def bayesian_path_probability(
    edge_weights: list[float],
    prior_success_rate: float = 0.5,
    num_samples: int = 2000,
) -> dict[str, float]:
    jax, jnp = _load_jax()
    numpyro, dist, MCMC, NUTS = _load_numpyro()

    edge_weights_arr = jnp.array(edge_weights)

    def model(weights: Any) -> None:
        base_prob = numpyro.sample(
            "base_prob",
            dist.Beta(prior_success_rate * 10, (1 - prior_success_rate) * 10),
        )
        path_prob = base_prob * jnp.prod(weights)
        numpyro.sample("obs", dist.Bernoulli(path_prob), obs=jnp.ones(1))

    kernel = NUTS(model)
    mcmc = MCMC(kernel, num_warmup=500, num_samples=num_samples)
    mcmc.run(jax.random.PRNGKey(0), edge_weights_arr)
    samples = mcmc.get_samples()

    path_probs = samples["base_prob"] * float(jnp.prod(edge_weights_arr))

    return {
        "mean": float(jnp.mean(path_probs)),
        "std": float(jnp.std(path_probs)),
        "ci_lower": float(jnp.percentile(path_probs, 2.5)),
        "ci_upper": float(jnp.percentile(path_probs, 97.5)),
    }
