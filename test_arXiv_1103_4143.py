################################################################################
## Purpose is to check the code against the results obtained by 
## J. Grande and L. Perivolaropoulos 
## Phys. Rev. D. 84:023514, 2011 
## Their mathematica code can be downloaded from http://leandros.physics.uoi.gr/ide/
## ****************************************************************************
## LTB_ScaleFactor can not be checked because it only applies to a cosmological 
## constant and not inhomogeneous dark energy. But LTB_geodesics along with 
## the method of getting the monopole, dipole, quadrupole moments using healpix can be 
## checked againsts numbers and plots in J. Grande and L. Perivolaropoulos. 
##
## NOTE: Eq. (3.4) in arXiv 1103.4143 is not from the IDE model (inhomogeneous 
## dark energy ) but something they took out from a reference paper.
## The model parameters for Eq. (3.7) are OmegaX_in = 0.699, OmegaM_in = 1-0.699, 
## r_obs = 30Mpc, r0 = 3.37 Gpc, delta_r = 0.35*Gpc
## Fig: 7, 9 and 10 are relevant figures.
## I thought I would get numbers that match exactly (apart from tiny differences 
## due to numerical errors). 
## But instead I rougly agree with the numbers in arXiv 1103.4143.
## While I solve for 100 or 200 different directions from 0. to 0.999*Pi 
## (For angle=Pi exactly the light ray travels inwards and hits the singularity 
## at the  center and should be avoided) before using splines to 
## get z_lastscattering(r_obs,angle) I notice that Grande and  Perivolaropoulos 
## only solve for nine different directions before using interpolation tables.  
## This will result in errors in their work. See Figures7to10.nb of their
## mathematica code. The uncertainties they quote are certainly underestimated
## by a factor which could be as large as 10 in some cases.
## NOTE: 
# Set ell_d=0 and bee_d = 90 to get theta=0, phi=0
# in get_GP_angles(ell=ras, bee=dec,ell_d = 51.7, bee_d = -24.9)
## and the manual spherical harmonic decomposition agrees with Healpix 
## because the change of coordinates is along the z-axis and gamma=xi=theta
## ************************************************************]
## notation r_obs == loc. 
## Best to redirect the output to a file
################################################################################ 

from __future__ import division
import numpy as np
from LTB_Sclass_v2 import LTB_ScaleFactor
from LTB_Sclass_v2 import LTB_geodesics, sample_radial_coord
from LTB_housekeeping import c, Mpc, Gpc, ageMpc
from LTB_housekeeping import Findroot, Integrate
from GP_profiles import GP_MODEL, get_GP_angles

from scipy.interpolate import UnivariateSpline as spline_1d
from scipy.interpolate import RectBivariateSpline as spline_2d
from matplotlib import pylab as plt
from mpl_toolkits.mplot3d import Axes3D

from joblib import Parallel, delayed
from joblib.pool import has_shareable_memory
import multiprocessing as mp

import healpy as hp

OmegaX_in = 0.699
OmegaM_in = 1. - OmegaX_in
test_GP = GP_MODEL(OmegaM_in=OmegaM_in,OmegaM_out=1., 
	               OmegaX_in = OmegaX_in,OmegaX_out=0.,
	               r0=3.37*Gpc,delta_r=0.35*Gpc,age=13.7*ageMpc)#r0=3.37*Gpc
print test_GP.__doc__

test_r_vals = np.array([0.,0.3,0.9,1.1,10.,2.e3,3.36e3,3.37e3,3.38e3,1e4])
print test_GP.OmegaM(test_r_vals)
print "d_OmegaM_dr"
print test_GP.d_OmegaM_dr(test_r_vals)
print "OmegaX"
print test_GP.OmegaX(test_r_vals)
print "d_OmegaX_dr"
print test_GP.d_OmegaX_dr(test_r_vals)

print "H0overc"
#print test_GP.H0overc(0.2,0.8,0.)
print test_GP.H0overc(0.)

#Now make splines for M(r), dM_dr(r), H(r), dH_dr(r), p(r), dp_dr(r). 
#Splines will be much faster 
#than the direct computation done in GP_profiles. Note that since E(r), dE_dr(r) 
#are zero only M(r), dM_dr(r), H(r), dH_dr(r) and Lambda are needed for solving
#the background and geodesic equations.
# r_vec is used to make splines
# r_vector is used for making the t-r grid on which the background LTB equations 
# are solved.
# r_vec has many more points than r_vector 
r_vec = sample_radial_coord(r0=test_GP.r0,delta_r=test_GP.delta_r,r_init=1e-10,
                            r_max=15.*1e3,num_pt1=2000,num_pt2=2000)
#r_vector = sample_radial_coord(r0=r0,delta_r=delta_r,r_init=1e-4,r_max=20*1e3,num_pt1=100,num_pt2=100)
size_r_vec = r_vec.size
r_vector = sample_radial_coord(r0=test_GP.r0,delta_r=test_GP.delta_r,r_init=1e-5,
                              r_max=15.*1e3,num_pt1=120,num_pt2=100)#r_init=1e-4
size_r_vector = r_vector.size

M_GP    = test_GP.M(r_vec)
H_GP    = test_GP.H0overc(r_vec)
p_GP    = test_GP.p(r_vec)
sp_M    = spline_1d(r_vec, M_GP, s=0)
sp_dMdr = sp_M.derivative(1)
sp_dMdr = spline_1d(r_vec,sp_dMdr(r_vec))
sp_H    = spline_1d(r_vec, H_GP, s=0)
sp_dHdr = sp_H.derivative(1) 
sp_dHdr = spline_1d(r_vec,sp_dHdr(r_vec))
sp_p    = spline_1d(r_vec,p_GP, s=0)
sp_dpdr = sp_p.derivative(1)
sp_dpdr = spline_1d(r_vec,sp_dpdr(r_vec))

def sp_E(r):
	return 0.
def sp_dEdr(r):
	return 0.

#plt.figure()
#plt.plot(r_vec,sp_M(r_vec))
#plt.figure()
#plt.plot(r_vec,sp_dMdr(r_vec))
#plt.figure()
#plt.plot(r_vec,sp_H(r_vec))
#plt.figure()
#plt.plot(r_vec,sp_dHdr(r_vec))
#plt.figure()
#plt.plot(r_vec,sp_p(r_vec))
#plt.show()

if (sp_p(r_vec).any() < 0.):
	print "o yeah a negative number "

model_age = test_GP.t0

def model_background(t,r):
	"""
	One can use the analytical form of R(t,r) to find all its derivatives.
	However, diff(R(t,r),r) found from R(t,r) has problems with 
	over and under flowing numbers. OmegaX(r) = 1 - OmegaM(r) seems to be 
	the culprit. It is best to avoid calculating diff(R(t,r),r) and 
	diff(R(t,r),t,r) here and instead use the spline interpolations to find 
	them from R(t,r) and diff(R(t,r),t). The simplest check is that 
	R(t0,r)=r and diff(R(t,r),r) at t=t0 should be unity. 
	"""
	sinh_t = np.sinh(np.sqrt(6.*sp_p(r)) * t)
	if ( sp_p(r) < 0.):
		print "is nan", r, sp_p(r)
	cosh_t = np.cosh(np.sqrt(6.*sp_p(r)) * t) 
	# R(t,r)
	R = 3./4.*sp_M(r)* sinh_t**2 / sp_p(r)
	R = R**(1./3.)
	# diff( R(t,r), t)
	Rdot = 6**(5./6.)/3. * ( sp_M(r)/sp_p(r) )**(1./3.) * np.sqrt( sp_p(r) ) \
	       *cosh_t / sinh_t**(1./3.)
	
	return R, Rdot

t_num_pt = 1000 #6000
t_vec = np.logspace(np.log10(1e-6),np.log10(model_age),num=t_num_pt,endpoint=True)
R_vec, Rdot_vec, Rdash_vec, Rdashdot_vec, = \
              [np.zeros((size_r_vector,t_num_pt)) for i in xrange(4)]

##serial 
##for i, r_loc in zip(range(len(r_vector)),r_vector):
##	print r_loc
##	t_vec[i,:], R_vec[i,:], Rdot_vec[i,:], Rdash_vec[i,:], Rdotdot_vec[i,:], \
##	Rdashdot_vec[i,:] = LTB_model0(r_loc=r_loc,num_pt=num_pt)
##	r_vec[i,:] = r_vec[i,:] + r_loc

def r_loop(r_loc):
	return model_background(t_vec,r_loc)


num_cores = mp.cpu_count()-1	
r = Parallel(n_jobs=num_cores,verbose=0)(delayed(r_loop)(r_loc) for r_loc in r_vector)

i = 0
for tup in r:
	R_vec[i,:], Rdot_vec[i,:] = tup
	i = i + 1

t_vector = t_vec
spR = spline_2d(r_vector,t_vector,R_vec,s=0)
spRdot = spline_2d(r_vector,t_vector,Rdot_vec,s=0)
i = 0
for r_val in r_vector:
	Rdash_vec[i,:] =  spR.ev(r_val,t_vector,dx=1,dy=0)
	Rdashdot_vec[i,:] = spRdot.ev(r_val,t_vector,dx=1,dy=0)
	i = i + 1

spRdash = spline_2d(r_vector,t_vector,Rdash_vec,s=0)
spRdashdot = spline_2d(r_vector,t_vector,Rdashdot_vec,s=0)


print "A basic check on the Hubble expansion "
print "The simplest check is that R(t0,r)=r and diff(R(t,r),r) at t=t0 should be unity."
for r_val in r_vector:
	print "H(r,t0) ", r_val, sp_H(r_val), spRdot.ev(r_val,model_age)/spR.ev(r_val,model_age)
	print "R(r,t0) ", r_val, spR.ev(r_val, model_age), spRdash.ev(r_val, model_age),spR.ev(r_val, model_age,dx=1,dy=0)

################################################################################
##******************************************************************************
model_geodesics =  LTB_geodesics(R_spline=spR,Rdot_spline=spRdot,
Rdash_spline=spRdash,Rdashdot_spline=spRdashdot,LTB_E=sp_E, LTB_Edash=sp_dEdr)

num_angles = 100  #200 #100
#angles = np.linspace(0.,0.999*np.pi,num=num_angles,endpoint=True)
#angles = np.linspace(0.,0.999*np.pi,num=num_angles,endpoint=True)
## In principle only the range 0 to pi is required. However with angle set to pi 
## the null ray is travelling radially inwards and hits the singularity at the void 
## center. But because when taking spherical harmonics the angle pi appears in the 
## interpolating integral, one can
## just interpolate its value by going over the upper limit of pi.
angles = np.concatenate( (np.linspace(0.,0.996*np.pi,num=int(num_angles/2),endpoint=True), 
                        np.linspace(1.01*np.pi,2.*np.pi,num=int(num_angles/2),endpoint=False)))

num_z_points = model_geodesics.num_pt 
geo_z_vec = model_geodesics.z_vec

geo_affine_vec, geo_t_vec, geo_r_vec, geo_p_vec, geo_theta_vec = \
                        [np.zeros((num_angles,num_z_points)) for i in xrange(5)] 

loc = 30.*Mpc #30.*Mpc #654.*Mpc

##First for an on center observer calculate the time when redshift is 1100.
## For alpha = 0. the light ray is travelling radially outward
center_affine, center_t_vec, center_r_vec, \
center_p_vec, center_theta_vec = model_geodesics(rp=r_vector[0],tp=model_age,alpha=0.*np.pi,atol=1e-12,rtol=1e-10)#angles[-1] atol=1e-10,rtol=1e-8
sp_center_t = spline_1d(geo_z_vec,center_t_vec,s=0)
print "age at t(z=1100) for central observer is ", sp_center_t(1100.)

##serial version
##for i, angle in zip(xrange(num_angles),angles):
##	geo_affine_vec[i,:], geo_t_vec[i,:], geo_r_vec[i,:], geo_p_vec[i,:], \
##	geo_theta_vec[i,:] = LTB_geodesics_model0(rp=loc,tp=model_age,alpha=angle)

##parallel version 2
def geo_loop(angle):
	return model_geodesics(rp=loc,tp=model_age,alpha=angle,atol=1e-10,rtol=1e-8)#atol=1e-10,rtol=1e-8

num_cores= mp.cpu_count()-1
geos = Parallel(n_jobs=num_cores,verbose=5)(
delayed(geo_loop)(angle=angle) for angle in angles)

i = 0
for geo_tuple in geos:
	geo_affine_vec[i,:], geo_t_vec[i,:], geo_r_vec[i,:], geo_p_vec[i,:], \
	geo_theta_vec[i,:] = geo_tuple
	i = i + 1

##finally make the 2d splines
sp_affine = spline_2d(angles,geo_z_vec,geo_affine_vec,s=0) 
sp_t_vec = spline_2d(angles,geo_z_vec,geo_t_vec,s=0)
sp_r_vec = spline_2d(angles,geo_z_vec,geo_r_vec,s=0)
sp_p_vec = spline_2d(angles,geo_z_vec,geo_p_vec,s=0)
sp_theta_vec = spline_2d(angles,geo_z_vec,geo_theta_vec,s=0)


ras, dec = np.loadtxt("pixel_center_galactic_coord_12288.dat",unpack=True)
Rascension, declination, gammas = get_GP_angles(ell=ras, bee=dec,ell_d = 51.7, bee_d = -24.9)

#z_of_gamma = np.empty_like(gammas)
z_star = 1100.
age_central = sp_center_t(z_star)
#age_central = sp_t_vec.ev(np.pi,z_star)
print "age at t(0.,z=1100) for central observer is ", age_central
@Findroot
def z_at_tdec(z,gamma):
	return sp_t_vec.ev(gamma,z)/age_central - 1.

z_at_tdec.set_options(xtol=1e-8,rtol=1e-8)#(xtol=1e-8,rtol=1e-8)
z_at_tdec.set_bounds(z_star-20.,z_star+20.) 
##Because Job lib can not pickle z_at_tdec.root directly
def z_at_tdec_root(gamma):
	return z_at_tdec.root(gamma)

z_of_angles = Parallel(n_jobs=num_cores,verbose=0)(delayed(z_at_tdec_root)(gamma) for gamma in angles)
z_of_angles = np.asarray(z_of_angles)

z_of_angles_sp = spline_1d(angles,z_of_angles,s=0)
z_of_gamma = z_of_angles_sp(gammas) 
#z_of_gamma = 1100. - (age_central-sp_t_vec.ev(gammas,1100.))/sp_t_vec.ev(gammas,1100.,dy=1)
np.savetxt("zGP_of_gamma_1000.dat",zip(z_of_gamma,sp_t_vec.ev(gammas,z_of_gamma)))

#All 3 methods give pretty much the same result
# method 1 to get my_map
#my_map = (z_of_gamma.mean() - z_of_gamma)/(1.+z_of_gamma)
# method 2 to get my_map
#my_map = (hp.pixelfunc.fit_monopole(z_of_gamma) - z_of_gamma)/(1.+z_of_gamma)
# method 3 to get my_map is Eq. (2.47) in arXiv 1103.4143
@Integrate
def get_bar_z(gamma,robs):
	return np.sin(gamma)/(1.+z_of_angles_sp(gamma))
get_bar_z.set_options(epsabs=1.49e-16,epsrel=1.49e-12)
get_bar_z.set_limits(0.,np.pi)
my_map = ( (2./get_bar_z.integral(loc)-1.) - z_of_gamma)/(1.+z_of_gamma)
print "bar_z Eq(2.47) ", 2./get_bar_z.integral(loc)-1., z_of_gamma.mean()

#############
#using spherical harmonics decomposition
############
z_mean = 2./get_bar_z.integral(loc) - 1.
def Delta_T(xi):
	"""
	0<= xi <= pi 
	"""
	return 2.7255*(z_mean - z_of_angles_sp(xi))/(1.+z_of_angles_sp(xi))

from scipy.special import legendre as legendre

@Integrate
def al0(xi,ell):
	"""
	For m=0
	Ylm = 1/2 sqrt((2l+1)/pi) LegendreP(l,x)
	xi: angle in radians
	Note: The integral over the other angle gives a factor of 2pi.
	While healpix does the spherical harmonic decomposition w.r.t spherical 
	polar coordinates (theta,phi), this manual decomposition is w.r.t the 
	angle (xi,phi) and xi is not theta.
	"""
	LegPol = legendre(ell)
	return 2.*np.pi*Delta_T(xi)*np.sqrt((2.*ell+1.)/(4.*np.pi))*LegPol(np.cos(xi))*np.sin(xi)

al0.set_options(epsabs=1.49e-10,epsrel=1.49e-8)
al0.set_limits(0.,np.pi)
print "\n One has to be careful as to how the spherical harmonics are normalized"
print "There are atleast three different ways adopted in literature"
print " now manually calculating alms , divide by 2.7255 to get dimensionless"
print "alm , l=0, m=0", al0.integral(0), al0.integral(0)/2.7255
print "alm , l=1, m=0", al0.integral(1), al0.integral(1)/2.7255
print "alm , l=2, m=0", al0.integral(2), al0.integral(2)/2.7255

flip = 'astro' # 'geo'
hp.mollview(map = my_map, title = "temp_map" ,
flip = flip,format='%.4e') 
hp.mollview(map = my_map, title = "temp_map" ,
flip = flip, remove_mono=True,format='%.4e') 
hp.mollview(map = my_map, title = "temp_map_no_dipole" ,
flip = flip, remove_dip=True,format='%.4e')
plt.show()

cls,alm = hp.sphtfunc.anafast(my_map,mmax=0,lmax=10,pol=False,alm=True)
print "checking with C_l = abs(al0)^2/(2l+1)"
ells = np.arange(cls.size)
print np.sqrt(np.abs(cls) * (2.*ells +1.))
print "double check with anafast"
print 'alm ', alm
print 'cls ', cls
print "a third check with map2alm"
alms = hp.map2alm(my_map,mmax=0,lmax=10).real
for i, alm in zip(xrange(alms.size),alms):
	print "m=0 is Fixed. ell %i  alm %5e" %(i, alm)
