# Ant Colony Foraging MDP - GNN specification
# Generalized Notation Notation (GNN) specification of the stigmergic ant-colony
# foraging MDP implemented in ants.py (Friedman et al., 2021).
# Validated against the pinned GNN revision in gnn/upstream.json.

## GNNSection
ActInfPOMDP

## GNNVersionAndFlags
GNN v1

## ModelName
Ant Colony Foraging MDP

## ModelAnnotation
Single-ant decision process for the 40x40 T-maze of Friedman et al. (2021),
"Active Inferants: An Active Inference Framework for Ant Colony Behavior"
(Front. Behav. Neurosci. 15:647732). Colony behaviour emerges from many ants
sharing one pheromone field.

- 9 hidden states: the 3x3 focal area around the ant (config.FOCAL_AREA).
- 10 observations: discrete pheromone levels 0..9 (config.NUM_OBSERVATIONS).
- 9 actions: the 8 neighbouring displacements plus staying in place
  (config.ACTION_MAP); action index a moves the ant onto focal cell a.

The likelihood A is not constant: the environment rebuilds it every step from
the shared pheromone field (each column of A is a one-hot over the pheromone
level of that focal cell). The declared A is the initial condition of a fresh
environment, where every cell is level 0. D is the uniform prior over focal
cells; the implementation replaces it at reset with the first-observation
posterior softmax(ln A[o, :]). E is the habit prior against staying in place;
the implementation additionally applies a dynamic log-prior (-20) against
immediately reversing the previous action.

## StateSpaceBlock
# Likelihood matrix: A[pheromone_level, focal_cell]
A[10,9,type=float]      # Observation likelihood (environment-dependent; initial condition declared)
# Transition tensor: B[next_state, previous_state, action]
B[9,9,9,type=float]     # Deterministic focal-cell transitions
# Preference vector: C[pheromone_level]
C[10,type=float]        # Log-preference weights over pheromone levels
# Initial state prior: D[focal_cell]
D[9,type=float]         # Prior over initial focal cells
# Habit vector: E[action]
E[9,type=float]         # Initial policy prior (habit) over actions
# Hidden state
s[9,1,type=float]       # Current focal-cell belief
s_prime[9,1,type=float] # Next focal-cell belief
# Observation
o[10,1,type=int]        # Current pheromone-level observation (index)
# Policy and control
pi[9,type=float]        # One-step policy posterior over actions
u[1,type=int]           # Action taken
G[9,type=float]         # Expected free energy per action
# Time
t[1,type=int]           # Discrete time step

## Connections
D>s
s-A
A-o
s-B
s>s_prime
B>u
C>G
E>pi
G>pi
pi>u
u>s_prime

## InitialParameterization
# A: 10 observations x 9 hidden states. Initial condition of a fresh
# environment (all cells at pheromone level 0): row 0 is all ones. The
# environment replaces each column with a one-hot vector for the cell's
# current pheromone level as trails are deposited.
A={
  (1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0),
  (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
  (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
  (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
  (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
  (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
  (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
  (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
  (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
  (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
}

# B: 9 next states x 9 previous states x 9 actions. Canonical orientation
# (next_state, previous_state, action); within each next-state slice, rows are
# previous states and columns are actions. Action a deterministically sets the
# next focal-cell state to a (ants.py::create_ant sets B[a, a, :] = 1.0), so
# column a of slice next_state=a is all ones and every other entry is zero.
B={
  (
    (1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    (1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    (1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    (1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    (1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    (1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    (1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    (1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    (1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
  ),
  (
    (0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    (0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    (0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    (0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    (0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    (0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    (0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    (0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    (0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
  ),
  (
    (0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
  ),
  (
    (0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0)
  ),
  (
    (0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0)
  ),
  (
    (0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0)
  ),
  (
    (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0)
  ),
  (
    (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0),
    (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0),
    (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0),
    (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0),
    (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0),
    (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0),
    (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0),
    (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0),
    (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
  ),
  (
    (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0),
    (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0),
    (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0),
    (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0),
    (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0),
    (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0),
    (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0),
    (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0),
    (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0)
  ),
}

# C: 10 observations. Log-preference weights. The implementation normalizes
# its raw preference vector C_raw = (0,1,2,3,4,5,6,7,8,9) plus p0 = exp(-16)
# into a distribution C_impl = normalize(C_raw + p0) and scores actions with
# the risk term KL(Q(o) || C_impl); softmax(C) recovers C_impl exactly, so
# these entries are ln(C_impl).
C=(-19.806663, -3.806662, -3.113515, -2.708050, -2.420368, -2.197225, -2.014903, -1.860752, -1.727221, -1.609438)

# D: 9 states. Uniform prior over the focal cells (1/9 each).
D=(0.111111, 0.111111, 0.111111, 0.111111, 0.111111, 0.111111, 0.111111, 0.111111, 0.111111)

# E: 9 actions. Habit prior from the implementation's static log-penalty of
# -20 against staying in place (action 4): softmax((0,0,0,0,-20,0,0,0,0)).
E=(0.125000, 0.125000, 0.125000, 0.125000, 2.576442e-10, 0.125000, 0.125000, 0.125000, 0.125000)

## Equations
# Generative model of the single ant:
#   o_t ~ Categorical(A[:, s_t])   # pheromone level observed at the focal cells
#   s_t+1 = a_t                    # action a moves the ant onto focal cell a
# State inference (single step, no planning):
#   s_t = softmax(ln A[o_t, :])
#   s_t+1 = softmax(ln(B[u_t] @ s_t))
# Policy inference (one-step expected free energy, SCALE = 10):
#   Q(o | a) = normalize(A @ B[a] @ s_t)
#   G(a) = KL(Q(o | a) || C) / SCALE
#   Q(pi) = softmax(-G + ln E - 20 * [a = previous action])
# Action selection: u_t ~ Categorical(Q(pi))

## Time
Dynamic
DiscreteTime=t
ModelTimeHorizon=2000

## ActInfOntologyAnnotation
A=LikelihoodMatrix
B=TransitionMatrix
C=LogPreferenceVector
D=PriorOverHiddenStates
E=Habit
G=ExpectedFreeEnergy
s=HiddenState
s_prime=NextHiddenState
o=Observation
pi=PolicyVector
u=Action
t=Time

## ModelParameters
num_hidden_states: 9
num_obs: 10
num_actions: 9
num_timesteps: 2000

## Footer
Ant Colony Foraging MDP v1 - GNN representation of ants.py (Friedman et al., 2021).
Single-step perception and action selection; colony-level behaviour emerges from
the shared pheromone field.

## Signature
pending
