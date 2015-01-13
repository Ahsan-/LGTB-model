#!/usr/bin/env python2.7
#from __future__ import division
import numpy as np
from scipy.integrate import ode, odeint


class Szekeres_geodesics():
	"""
	Solves the geodesics for an off center observer Eq. (3.19)-(3.20) in 
	``Structures in the Universe by Exact Method`` by Krzystof Bolejko etal.
	"""
	def __init__(self, R_spline,Rdot_spline,Rdash_spline,Rdashdot_spline,LTB_E, LTB_Edash,num_pt=1600, *args, **kwargs):
		self.R         = R_spline
		self.Rdot      = Rdot_spline
		self.Rdash     = Rdash_spline
		self.Rdashdot  = Rdashdot_spline
		self.args      = args
		self.kwargs    = kwargs
		self.E         = LTB_E
		self.Edash     = LTB_Edash
		# i stands for integer index
		self.i_lambda = 0; self.i_t = 1; self.i_r = 2; self.i_p = 3; self.i_theta = 4
		#self.i_z = 0; self.i_t = 1; self.i_r = 2; self.i_p = 3; self.i_theta = 4
		#setup the vector of redshifts
		self.num_pt = num_pt
		self.z_vec = np.empty(num_pt)
		self._set_z_vec()
	
	def _set_z_vec(self):
		"""
		vector of redshifts at which points the geodesics are saved
		"""
		atleast = 100
		atleast_tot = atleast*4+1200
		
		if not isinstance(self.num_pt, int):
			raise AssertionError("num_pt has to be an integer")		
		elif self.num_pt < atleast_tot:
			raise AssertionError("Senor I assume at least 1600 points distributed \
			between z=0 and z=3000")
		
		bonus = self.num_pt - atleast_tot 
		#insert the extra points between z=10 and 3000
		z = np.linspace(0.,0.01,num=atleast,endpoint=False)
		z = np.concatenate((z, np.linspace(0.01,0.1,num=atleast,endpoint=False)))
		z = np.concatenate((z, np.linspace(0.1,1.,num=atleast,endpoint=False)))
		z = np.concatenate((z, np.linspace(1.,10.,num=atleast,endpoint=False)))
		z = np.concatenate((z, np.linspace(10.,3000.,
		                    num=atleast_tot-4*atleast+bonus,endpoint=True)))
		
		self.z_vec = z
		return


	def Szekeres_geodesic_derivs_odeint(self,y,t,J):
		"""
		Returns the derivatives w.r.t redshift ``tau``, [tau]=Mpc, for 
		diff(t(tau),tau), diff(r(tau),tau), diff(t(tau),tau,tau) of Eq. (3.19)-(3.20) in 
		``Structures in the Universe by Exact Method`` by Krzystof Bolejko etal.
		Rps:
		    denotes R_p * sin(alpha) = R_p(t_p, r_p) * sin(alpha)
		ktp: 
		    k^t_p which is set to 1 or -1 is the measured energy of the photon
		    at the observer position. It is set to one because its magnitude does 
		    not matter, only its fractional change matters.    
		caution: 
		        In general avoid alpha=pi/2 and 3/2*pi which means the light would
		        be travelling perpendicular to the axis joining the observer and 
		        the center of symmetry.
		"""
		dy_dt = np.empty_like(y)
		
		H, H_t, H_r, H_p, H_q, F, F_t, F_r, F_p, F_q = get_H_F_and_derivs()
		 
		dt_ds = y[4]
		dr_ds = y[5]
		dp_ds = y[6]
		dq_ds = y[7]
		
		ddt_dss = H*H_t * dr_ds**2 + F*F_t* ( dp_ds**2 + dq_ds**2 )
		ddt_dss = -ddt_dss

		ddr_dss = H_r/H * dr_ds**2 + 2.*H_p/H*dr_ds* (dp_ds + dq_ds) + \
		          2.*H_t/H*dr_ds*dt_ds - F*F_r/H**2 *(dp_ds**2 + dq_ds**2)  
		ddr_dss = -ddr_dss
		
		ddq_dss = -H*H_q/F**2*dr_ds**2 + 2.*F_r/F*dr_ds*dq_ds \
		          -F_q/F*dp_ds**2 + 2.*F_p/F*dp_ds*dq_ds + F_q/F*dq_ds**2 \
		          +2.*F_t/F*dq_ds*dt_ds
		ddq_dss = -ddq_dss
		
		ddp_dss = -H*H_p/F**2*dr_ds**2 + 2.*F_r/F*dr_ds*dp_ds + F_p/F*dp_ds**2 \
		          +2.*F_q/F*dp_ds*dq_ds + 2.*F_t/F*dp_ds*dt_ds - 2.*F_p/F*dq_ds**2
		ddp_dss = -ddp_dss
		
		dlnDA_ds = H_t/H+2.*F_t/F
		return 
			
	def __call__(self,rp=45.,tp=0.92,alpha=np.pi/6.,atol=1e-12,rtol=1e-10):
		y_init = np.zeros(5)
		p0 = np.cos(alpha)*np.sqrt(1.+2*self.E(rp))/self.Rdash.ev(rp,tp); J = rp*np.sin(alpha)
		y_init[0]=0.; y_init[1]=tp; y_init[2]=rp; y_init[3]=p0; y_init[4] = 0.
		
		print "R(rp,tp) = ", self.R.ev(rp,tp), rp, tp, alpha, self.Rdash.ev(rp,tp)
		#print "alpha, sign ", alpha, sign
		z_init = 0.
		#evolve_LTB_geodesic = ode(self.LTB_geodesic_derivs).set_integrator('vode', method='adams', with_jacobian=False,atol=atol, rtol=rtol)
		#evolve_LTB_geodesic.set_initial_value(y_init, z_init).set_f_params(J)
		print 'init_conds ', y_init, z_init, self.Rdash.ev(rp,tp), self.R.ev(rp,tp), 'loc ', rp
		#print "and derivs ", self.LTB_geodesic_derivs(t=0.,y=y_init,J=J)
		print "E, Edash, J ", self.E(rp), self.Edash(rp), J
	
		z_vec = self.z_vec # could just use self.z_vec itself
		print "ding "#, z_vec
		
		odeint_ans = odeint(func=self.LTB_geodesic_derivs_odeint,y0=y_init,t=z_vec,
		args=(J,),Dfun=None,full_output=0,rtol=rtol,atol=atol)
		#use odeint_ans, myfull_out  when setting full_output to True
		print  odeint_ans[-1,self.i_lambda],odeint_ans[-1,self.i_t], \
		odeint_ans[-1,self.i_r], odeint_ans[-1,self.i_p], odeint_ans[-1,self.i_theta]
		#self.i_lambda = 0; self.i_t = 1; self.i_r = 2; self.i_p = 3; self.i_theta = 4
		return odeint_ans[:,self.i_lambda],odeint_ans[:,self.i_t], \
		odeint_ans[:,self.i_r], odeint_ans[:,self.i_p], odeint_ans[:,self.i_theta]




