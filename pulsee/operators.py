import numpy as np
from qutip import Qobj
from scipy.constants import Planck, Boltzmann
from tqdm import tqdm


def exp_diagonalize(q):
    """
    Diagonalizes the given operator, and exponentiates the diagonal eigenvalue
    matrix. 

    Parameters
    -----------
    q : Qobj

    Returns
    --------
    A list of Qobjs including the eigenvector matrix, the diagonal eigenvalue 
    matrix, and the exponent of the diagonal eigenvalue matrix. 
    """
    eigvals, eigvects = q.eigenstates()
    d = np.zeros((len(eigvals), len(eigvals)), dtype=np.complex128)
    dexp = np.zeros((len(eigvals), len(eigvals)), dtype=np.complex128)

    i = 0
    for e in eigvals:
        d[i, i] = e
        dexp[i, i] = np.exp(e)
        i += 1

    d = Qobj(d)
    dexp = Qobj(dexp)
    u = Qobj(np.concatenate(eigvects, axis=1))

    return u, d, dexp


def changed_picture(q, h_change_of_picture, time, invert=False):
    """
    Casts the operator either in a new picture generated by the Operator h_change_of_picture or
    back to the Schroedinger picture, according to the parameter invert.

    Parameters
    ----------
    q : Qobj
    h_change_of_picture : Qobj
        Operator which generates the change to the new picture. Typically,
        this operator is a term of the Hamiltonian (measured in MHz).
    time : float
        Instant of evaluation of the operator in the new picture, expressed in microseconds.
    invert : bool
        When it is False, the owner Operator object is assumed to be expressed in the
        Schroedinger picture and is converted into the new one.
        When it is True, the owner object is thought in the new picture and the
        opposite operation is performed.

    Returns
    -------
    A new Operator object equivalent to the owner object but expressed in a different picture.
    """
    t = Qobj(-1j * 2 * np.pi * h_change_of_picture * time)
    if invert:
        t = -t
    return t.expm() * q * (t.expm()).dag()


def unit_trace(q):
    """
    Returns a boolean which expresses whether the trace of the operator is equal to 1,
    within a relative error tolerance of 10<sup>-6</sup>.
    Parameters
    ----------
    q : Qobj

    Returns
    -------
    True, when unit trace is verified.
    False, when unit trace is not verified.
    """
    return np.isclose(q.tr(), 1, rtol=1e-6)


def positivity(q):
    """
    Returns a boolean which expresses whether the operator is a positive operator,
    i.e. its matrix has only non-negative eigenvalues 
    (taking the 0 with an error margin of 10^(-10)).

    Parameters
    ----------
    q : Qobj

    Returns
    -------
    True, when positivity is verified.
    False, when positivity is not verified.
    """
    eigenvalues = q.eigenenergies()
    return np.all(np.real(eigenvalues) >= -1e-10)


def apply_op(q, U):
    """
    Applies the operator U onto the density matrix q

    Parameters
    ----------
    q : Qobj

    Returns
    -------
    apply_op(U) = U * dm * U_dagger
    """
    return U * q * U.dag()


def apply_exp_op(q, U):
    """
    Applies the operator U.expm() onto the density matrix q

    Parameters
    ----------
    q : Qobj

    Returns
    -------
    apply_op(U) = U.expm() * dm * U.expm()_dagger
    """
    return U.expm() * q * (U.expm()).dag()


def evolve_by_hamiltonian(dm, static_hamiltonian, time):
    """
    Returns the density matrix represented by the owner object evolved through a
    time interval time under the action of the stationary Hamiltonian static_hamiltonian.

    Parameters
    ----------
    dm : QObj
        The initial density matrix
    static_hamiltonian : Qobj
        Observable or in general a hermitian Operator
        Time-independent Hamiltonian of the system, in MHz.
    time : float
        Duration of the evolution, expressed in microseconds.

    Returns
    -------
    A DensityMatrix object representing the evolved state converted to rads.
    """
    iHt = 1j * 2 * np.pi * static_hamiltonian * time
    # dm.transform(U) = U * dm * U_dagger
    # not sure if above is true
    return apply_exp_op(dm, iHt)


def random_operator(d):
    """
    Returns a randomly generated operator object of dimensions d.

    Parameters
    ----------
    d : int
        Dimensions of the Operator to be generated.

    Returns
    -------
    An Operator object whose matrix is d-dimensional and has random complex elements
    with real and imaginary parts in the half-open interval [-10., 10.].
    """
    round_elements = np.vectorize(round)
    real_part = round_elements(20 * (np.random.rand(d, d) - 1 / 2), 2)
    imaginary_part = 1j * round_elements(20 * (np.random.rand(d, d) - 1 / 2), 2)
    random_array = real_part + imaginary_part
    return Qobj(random_array)


def canonical_density_matrix(hamiltonian, temperature):
    """
    Returns the density matrix of a canonical ensemble of quantum systems at thermal equilibrium.

    Parameters
    ----------
    hamiltonian : Operator
        Hamiltonian of the system at equilibrium, expressed in MHz.
    temperature : positive float
        Temperature of the system in kelvin.

    Returns
    -------
    A DensityMatrix object which embodies the canonical density matrix.

    Raises
    ------
    ValueError, if temperature is negative or equal to zero.
    """
    if temperature <= 0:
        raise ValueError("The temperature must take a positive value")

    exponent = - (Planck / Boltzmann) * hamiltonian * 2 * np.pi * 1e6 / temperature
    numerator = exponent.expm()
    try:
        canonical_dm = numerator.unit()
    except ValueError:
        raise ValueError('Most likely exponent cannot be taken because the value is too large. '
                         'Either hamiltonian has a very strong interaction in MHz, or the temperature'
                         'is too low.')
    return canonical_dm


def calc_e_ops(dms, e_ops):
    """
    Returns the expectation value of the operators for each density matrix given.

    Parameters
    ----------
    dms : List
        List of Qobj of the density matrices.

    e_ops : List
        Operators

    Returns
    -------
    List of lists. For each e_op, its expectation value in the particulat dm.
    """
    exp_vals = [[] for x in range(len(e_ops))]
    for dm in tqdm(dms):
        for i in range(len(e_ops)):
            exp_vals[i].append((dm * e_ops[i]).tr())

    return np.array(exp_vals)


def apply_rot_pulse(rho, duration, rot_axis):
    """
    Apply a "pulse" to the given state by rotating the given state by  
    the given duration. i.e., transforms the density matrix by 
    `U = exp(- i * duration * rot_axis)`:
        `U * rho * U.dag()`

    Parameters:
    -----------
    rho : Qobj
        The density matrix of the state to apply the pulse to.
    duration : float
        The duration of the applied pulse as an angle in radians.
    rot_axis : Qobj
        Angular momentum operator for the corresponding axis of rotation. 

    Returns:
    --------
    The transformed density matrix as a Qobj. 
    """

    rot_op = (-1j * duration * rot_axis).expm()
    return apply_op(rho, rot_op)
    # return rho.transform((-1j * duration * rot_axis).expm())