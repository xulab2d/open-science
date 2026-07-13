**Observation**

Key local references supported by the supplied context:

1. **“Signatures of fractional charges via anyon-trions in twisted MoTe2”**  
   Local node: `paper:signatures_of_fractional_charges_via_anyon_trions_in_twisted_mote2`  
   Local shelves: `lab_assistant/knowledge/papers/moire_excitons_and_optics.md`, `lab_assistant/knowledge/papers/moire_tmote2.md`, `lab_assistant/knowledge/papers/xu_group_recent_moire_states.md`  
   Evidence: the context says PL trion-like complexes in twisted MoTe2 encode fractional quasiparticle charge, with binding-energy ratios tracking expected `e/3 : e/5` behavior.

2. **“Optical signatures of -1/3 fractional quantum anomalous Hall state in twisted MoTe2”**  
   Local node: `paper:arxiv_2602_04561v1`  
   Evidence: the context says this paper uses **PL** and **RMCD** to optically detect ferromagnetic states at `nu = -1`, `-2/3`, and `-1/3` in twisted MoTe2. One-hop graph edges also connect it to `concept:moire_filling`, `observable:pl`, and `observable:rmcd` in the excluded-budget list.

Exclude from the requested set:

- **“Nano-optical imaging of the tailored exciton-polariton transport in MoSe2 waveguides”**  
  Node: `paper:nano_optical_imaging_of_the_tailored_exciton_polariton_transport_in_mose2_wavegu`  
  Reason: exciton-polariton / waveguide paper; supplied context does not say it directly addresses moire trapping.

- **“Separation of the valley exciton-polariton in two-dimensional semiconductors with an anisotropic photonic crystal”**  
  Node: `paper:separation_of_the_valley_exciton_polariton_in_two_dimensional_semiconductors_wit`  
  Reason: exciton-polariton / photonic-crystal paper; supplied context does not say it directly addresses moire trapping.

**Inference**

The strongest local references for **moire exciton optical signatures** are the anyon-trion PL paper and the optical PL/RMCD FQAH paper, because both directly use optical excitonic observables in twisted MoTe2 moire systems. The polariton/waveguide papers look like false positives for “exciton optics” and should be filtered out for this query.

**Uncertainty**

The supplied context points to `lab_assistant/knowledge/papers/moire_excitons_and_optics.md` as the relevant shelf, but it does not include the full shelf contents. So this is the key reference set recoverable from the provided context, not a guaranteed exhaustive local bibliography.