# KVΔ experimental contract

KVΔ separates what is declared known from what is observed, then investigates what the declared knowledge failed to account for.

## Definitions

* K — known state. The variables, measurements, constraints, geometry, history, and other information explicitly declared as known for an experiment.
* V — resulting or observed state. The later measurable status or outcome the experiment is trying to account for.
* Δ — what K missed. The structure, factor, interaction, context, or condition not represented in K that is needed to better account for V.

Δ is not defined as:

* V − K
* K − V
* forecast error
* a numerical residual
* a generic difference term

A residual may show that K is incomplete, but the residual itself is not automatically Δ.

## Experiment record

Every experiment must declare:

* the exact contents of K
* the exact observable V
* the horizon between K and V
* region and depth
* source datasets and versions
* chronological discovery, validation, and sealed-test periods
* comparison baselines
* scoring functions
* any fitted parameters
* the procedure used to search for missing structure

## Discovery

The first task is to declare K and observe V.

Where K repeatedly fails to account for V, the experiment looks for repeatable structure in those failures.

That structure may suggest a candidate Δ.

During discovery, future V may be inspected because the purpose is explanatory: to identify what the original K may have missed.

## Candidate Δ

A candidate Δ should correspond to something meaningful that was absent from K.

Examples might include:

* recent history
* spatial context
* forcing from another system
* boundary effects
* seasonal state
* interaction between otherwise known variables

A candidate is not accepted merely because it correlates with the observed error.

## Revised K

Once a candidate missing factor has been identified, it must be represented using information available without looking at the target V.

That representation is then incorporated into a revised known state, K′.

The cycle is:

1. Declare K.
2. Observe V.
3. Locate systematic failures of K to account for V.
4. Propose what may have been missing.
5. Represent that candidate without using target-period V.
6. Add it to K′.
7. Test K′ on unseen data.

## Non-negotiable rule

Information derived from the target V may be used to discover a candidate Δ, but it may not be smuggled into K′ during validation or sealed evaluation.

Otherwise the result is retrospective explanation, not predictive evidence.

## Falsification

A proposed missing factor is unsupported when:

* adding its measurable representation to K does not improve the declared out-of-sample test;
* the apparent effect disappears on an independent interval or region;
* a simpler baseline explains the same result;
* or the candidate cannot be represented without using future information.

Negative results remain part of the project record.
