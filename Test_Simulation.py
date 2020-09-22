import numpy as np
import pandas as pd
import math

import matplotlib.pylab as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.pyplot import xticks, yticks

import hypothesis.strategies as st
from hypothesis import given, assume

from Operators import *

from Nuclear_Spin import *

from Hamiltonians import *

from Simulation import *


def test_null_zeeman_contribution_for_0_gyromagnetic_ratio():
    spin_par = {'quantum number' : 3/2,
                'gamma/2pi' : 0.}
    
    zeem_par = {'field magnitude' : 10.,
                'theta_z' : 0,
                'phi_z' : 0}
    
    quad_par = {'coupling constant' : 0.,
                'asymmetry parameter' : 0.,
                'alpha_q' : 0,
                'beta_q' : 0,
                'gamma_q' : 0}
    
    h_unperturbed = nuclear_system_setup(spin_par, zeem_par, quad_par)[1]
    
    null_matrix = np.zeros((4, 4))
    
    assert np.all(np.isclose(h_unperturbed.matrix, null_matrix, rtol=1e-10))
    
# Checks that if the initial density matrix is set to the (normalized) identity, the density matrix
# returned by the function Evolve will be as well close to the identity
def test_Evolution_Identity_Matrix():
    spin_par = {'quantum number' : 5/2,
                'gamma/2pi' : 1.}
    
    zeem_par = {'field magnitude' : 10.,
                'theta_z' : math.pi,
                'phi_z' : 0}
    
    quad_par = {'coupling constant' : 1.,
                'asymmetry parameter' : 0.5,
                'alpha_q' : 0,
                'beta_q' : math.pi/4,
                'gamma_q' : math.pi/4}
    
    identity = np.identity(6)/6
    
    spin, h_unperturbed, dm_initial = nuclear_system_setup(spin_par, zeem_par, quad_par, \
                                                     initial_state=identity)
    
    mode = pd.DataFrame([(10., 1., 0., math.pi/2, 0)], 
                        columns=['frequency', 'amplitude', 'phase', 'theta_p', 'phi_p'])
    
    RRF_par={'nu_RRF': 10,
             'theta_RRF': 0,
             'phi_RRF': 0}
    
    dm_evolved = Evolve(spin, h_unperturbed, dm_initial, \
                        mode, pulse_time=10, \
                        picture='RRF', RRF_par=RRF_par, \
                        n_points=10)
    
    assert np.all(np.isclose(dm_evolved.matrix, identity, rtol=1e-10))
    
# Checks that the Observable returned by RRF_Operator is proportional to the Operator I['z'] of the spin
# when the angle theta_RRF is set to 0
def test_RRF_Operator_Proportional_To_Iz():
    
    spin = Nuclear_Spin(3/2, 1.)
    
    RRF_par = {'nu_RRF': 10,
              'theta_RRF': 0,
              'phi_RRF': 0}
    
    rrf_o = RRF_Operator(spin, RRF_par)
    
    rrf_matrix = rrf_o.matrix
    Iz_matrix = spin.I['z'].matrix
    
    c = rrf_matrix[0, 0]/Iz_matrix[0, 0]
    
    assert np.all(np.isclose(rrf_matrix, c*Iz_matrix, rtol=1e-10))
    
# Checks that the number of frequencies of transition computed by Transition_Spectrum coincides with
# (2I)*(2I+1)/2
@given(s = st.integers(min_value=1, max_value=14))
def test_Number_Lines_Transition_Spectrum(s):
    
    spin_par = {'quantum number' : s/2,
                'gamma/2pi' : 1.}
    
    zeem_par = {'field magnitude' : 10.,
                'theta_z' : math.pi/4,
                'phi_z' : 0}
    
    quad_par = {'coupling constant' : 5.,
                'asymmetry parameter' : 0.3,
                'alpha_q' : math.pi/3,
                'beta_q' : math.pi/5,
                'gamma_q' : 0}
    
    spin, h_unperturbed, dm_0 = nuclear_system_setup(spin_par, zeem_par, quad_par)
    
    f, p = Transition_Spectrum(spin, h_unperturbed, normalized=False, dm_initial=dm_0)
    
    assert len(f)==(spin.d)*(spin.d-1)/2
    
# Checks that for very short relaxation times, the FID signal goes rapidly to 0
def test_Fast_Decay_FID_Signal():
    spin_par = {'quantum number' : 2,
                'gamma/2pi' : 1.}
    
    zeem_par = {'field magnitude' : 10.,
                'theta_z' : math.pi/4,
                'phi_z' : 0}
    
    quad_par = {'coupling constant' : 5.,
                'asymmetry parameter' : 0.3,
                'alpha_q' : math.pi/3,
                'beta_q' : math.pi/5,
                'gamma_q' : 0}
    
    initial_matrix = np.zeros((5, 5))
    initial_matrix[0, 0] = 1
    
    spin, h_unperturbed, dm_0 = nuclear_system_setup(spin_par, zeem_par, quad_par,
                                                     initial_state=initial_matrix)
    
    t, signal = FID_Signal(spin, h_unperturbed, dm_0, time_window=100, T2=1)
    
    assert np.absolute(signal[-1])<1e-10
    
# Checks that the Fourier transform of two FID signal acquired with a phase difference of pi are one the
# opposite of the other
def test_Opposite_Decay_Signal():
    spin_par = {'quantum number' : 3,
                'gamma/2pi' : 1.}
    
    zeem_par = {'field magnitude' : 10.,
                'theta_z' : math.pi/4,
                'phi_z' : 0}
    
    quad_par = {'coupling constant' : 5.,
                'asymmetry parameter' : 0.3,
                'alpha_q' : math.pi/3,
                'beta_q' : math.pi/5,
                'gamma_q' : 0}
    
    initial_matrix = np.zeros((7, 7))
    initial_matrix[0, 0] = 1
    
    spin, h_unperturbed, dm_0 = nuclear_system_setup(spin_par, zeem_par, quad_par,
                                                     initial_state=initial_matrix)
    
    mode = pd.DataFrame([(10., 1., 0., math.pi/2, 0)], 
                        columns=['frequency', 'amplitude', 'phase', 'theta_p', 'phi_p'])
    
    dm_evolved = Evolve(spin, h_unperturbed, dm_0, \
                        mode, pulse_time=10, \
                        picture='IP', \
                        n_points=10)
    
    t, signal1 = FID_Signal(spin, h_unperturbed, dm_evolved, time_window=250, T2=100)
    t, signal2 = FID_Signal(spin, h_unperturbed, dm_evolved, time_window=250, T2=100, phi=math.pi)
    
    f, fourier1 = Fourier_Transform_Signal(signal1, t, 7.5, 12.5)
    f, fourier2 = Fourier_Transform_Signal(signal2, t, 7.5, 12.5)
    
    assert np.all(np.isclose(fourier1, -fourier2, rtol=1e-10))

# Checks that the Fourier transform of the signal has the same shape both after adding the phase
# computed by Fourier_Phase_Shift directly to the FID signal and by rotating the detection coil by the
# same angle
def test_Two_Methods_Phase_Adjustment():
    spin_par = {'quantum number' : 3/2,
                'gamma/2pi' : 1.}
    
    zeem_par = {'field magnitude' : 10.,
                'theta_z' : 0,
                'phi_z' : 0}
    
    quad_par = {'coupling constant' : 0,
                'asymmetry parameter' : 0,
                'alpha_q' : 0,
                'beta_q' : 0,
                'gamma_q' : 0}
    
    initial_matrix = np.zeros((4, 4))
    initial_matrix[0, 0] = 1
    
    spin, h_unperturbed, dm_0 = nuclear_system_setup(spin_par, zeem_par, quad_par,
                                                     initial_state=initial_matrix)
    
    mode = pd.DataFrame([(10., 1., 0., math.pi/2, 0)], 
                        columns=['frequency', 'amplitude', 'phase', 'theta_p', 'phi_p'])
    
    dm_evolved = Evolve(spin, h_unperturbed, dm_0, \
                        mode, pulse_time=math.pi, \
                        picture='IP', \
                        n_points=10)
    
    t, fid = FID_Signal(spin, h_unperturbed, dm_evolved, time_window=500)
    f, fourier0 = Fourier_Transform_Signal(fid, t, 9, 11)
            
    phi = Fourier_Phase_Shift(f, fourier0, peak_frequency_hint=10)
    f, fourier1 = Fourier_Transform_Signal(np.exp(1j*phi)*fid, t, 9, 11)
            
    t, fid_rephased = FID_Signal(spin, h_unperturbed, dm_evolved, time_window=500, phi=-phi)
    f, fourier2 = Fourier_Transform_Signal(fid_rephased, t, 9, 11)
        
    assert np.all(np.isclose(fourier1, fourier2, rtol=1e-10))


    
    
    
    