#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Core Trinity model implementation.

The TrinityModel implements the universal phase transition formula:
Σ = α·S + β·D + γ·T + δ·(S×D) + ε·(D×T) + ζ·(S×T) + η·(S×D×T)
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.metrics import r2_score
from typing import Dict, Optional, Tuple, Union
import warnings


class TrinityModel(BaseEstimator, RegressorMixin):
    """
    Universal phase transition model using Surface-Depth-Time dimensions.
    
    Parameters
    ----------
    fit_interactions : bool, default=True
        Include pairwise interaction terms (δ, ε, ζ)
    fit_triple : bool, default=True
        Include triple interaction term (η). Required by theory.
    method : str, default='L-BFGS-B'
        Optimization method for coefficient fitting
    max_iter : int, default=1000
        Maximum optimization iterations
    
    Attributes
    ----------
    coefficients_ : dict
        Fitted coefficients {alpha, beta, gamma, delta, epsilon, zeta, eta}
    history_ : list
        Optimization history
    """
    
    def __init__(
        self,
        fit_interactions: bool = True,
        fit_triple: bool = True,
        method: str = 'L-BFGS-B',
        max_iter: int = 1000
    ):
        self.fit_interactions = fit_interactions
        self.fit_triple = fit_triple
        self.method = method
        self.max_iter = max_iter
        self.coefficients_ = None
        self.history_ = []
        
    def trinity_formula(
        self,
        S: Union[float, np.ndarray],
        D: Union[float, np.ndarray],
        T: Union[float, np.ndarray],
        coeffs: Optional[Dict[str, float]] = None
    ) -> Union[float, np.ndarray]:
        """
        Compute Σ = α·S + β·D + γ·T + interactions + triple.
        
        Parameters
        ----------
        S, D, T : float or array-like
            Surface, Depth, Time dimension values
        coeffs : dict, optional
            Coefficients to use. If None, uses fitted coefficients.
            
        Returns
        -------
        float or ndarray
            Σ values
        """
        if coeffs is None:
            if self.coefficients_ is None:
                raise ValueError("Model not fitted. Call fit() first or provide coeffs.")
            coeffs = self.coefficients_
            
        # Linear terms
        alpha = coeffs.get('alpha', 0)
        beta = coeffs.get('beta', 0)
        gamma = coeffs.get('gamma', 0)
        
        linear = alpha * S + beta * D + gamma * T
        
        # Pairwise interactions
        if self.fit_interactions:
            delta = coeffs.get('delta', 0)
            epsilon = coeffs.get('epsilon', 0)
            zeta = coeffs.get('zeta', 0)
            pairwise = delta * S * D + epsilon * D * T + zeta * S * T
        else:
            pairwise = 0
            
        # Triple interaction (the invariant)
        if self.fit_triple:
            eta = coeffs.get('eta', 0)
            triple = eta * S * D * T
        else:
            triple = 0
            
        return linear + pairwise + triple
    
    def _loss(self, params, S, D, T, target, sample_weight):
        """Compute MSE loss for optimization."""
        # Unpack parameters based on what's being fit
        idx = 0
        coeffs = {}
        
        # Linear terms always included
        coeffs['alpha'] = params[idx]; idx += 1
        coeffs['beta'] = params[idx]; idx += 1
        coeffs['gamma'] = params[idx]; idx += 1
        
        if self.fit_interactions:
            coeffs['delta'] = params[idx]; idx += 1
            coeffs['epsilon'] = params[idx]; idx += 1
            coeffs['zeta'] = params[idx]; idx += 1
            
        if self.fit_triple:
            coeffs['eta'] = params[idx]; idx += 1
            
        # Compute predictions
        pred = self.trinity_formula(S, D, T, coeffs)
        
        # Weighted MSE
        residuals = pred - target
        if sample_weight is not None:
            residuals = residuals * np.sqrt(sample_weight)
            
        return np.mean(residuals ** 2)
    
    def fit(
        self,
        S: Union[np.ndarray, pd.Series],
        D: Union[np.ndarray, pd.Series],
        T: Union[np.ndarray, pd.Series],
        target: Union[np.ndarray, pd.Series],
        sample_weight: Optional[np.ndarray] = None,
        initial_guess: Optional[Dict[str, float]] = None
    ) -> 'TrinityModel':
        """
        Fit coefficients to minimize variance of Σ - target.
        
        Parameters
        ----------
        S, D, T : array-like
            Surface, Depth, Time values (shape: n_samples,)
        target : array-like
            Target values to predict (e.g., risk, generalization gap)
        sample_weight : array-like, optional
            Sample weights for weighted fitting
        initial_guess : dict, optional
            Initial coefficient values. Default: small positive values.
            
        Returns
        -------
        self : TrinityModel
            Fitted model
        """
        # Convert to numpy arrays
        S = np.asarray(S, dtype=float)
        D = np.asarray(D, dtype=float)
        T = np.asarray(T, dtype=float)
        target = np.asarray(target, dtype=float)
        
        # Validate inputs
        if not (S.shape == D.shape == T.shape == target.shape):
            raise ValueError("S, D, T, target must have same shape")
            
        n_samples = len(S)
        if n_samples < 3:
            raise ValueError(f"Need at least 3 samples, got {n_samples}")
            
        # Build initial guess
        if initial_guess is None:
            # Start with small positive values
            x0 = [0.1, 0.1, 0.1]  # alpha, beta, gamma
            if self.fit_interactions:
                x0.extend([0.01, 0.01, 0.01])  # delta, epsilon, zeta
            if self.fit_triple:
                x0.append(0.001)  # eta
        else:
            x0 = [initial_guess.get('alpha', 0.1),
                  initial_guess.get('beta', 0.1),
                  initial_guess.get('gamma', 0.1)]
            if self.fit_interactions:
                x0.extend([initial_guess.get('delta', 0.01),
                          initial_guess.get('epsilon', 0.01),
                          initial_guess.get('zeta', 0.01)])
            if self.fit_triple:
                x0.append(initial_guess.get('eta', 0.001))
                
        # Optimize
        result = minimize(
            fun=self._loss,
            x0=x0,
            args=(S, D, T, target, sample_weight),
            method=self.method,
            options={'maxiter': self.max_iter, 'disp': False}
        )
        
        if not result.success:
            warnings.warn(f"Optimization did not converge: {result.message}")
            
        # Store coefficients
        idx = 0
        self.coefficients_ = {
            'alpha': result.x[idx],
            'beta': result.x[idx + 1],
            'gamma': result.x[idx + 2]
        }
        idx = 3
        
        if self.fit_interactions:
            self.coefficients_.update({
                'delta': result.x[idx],
                'epsilon': result.x[idx + 1],
                'zeta': result.x[idx + 2]
            })
            idx += 3
            
        if self.fit_triple:
            self.coefficients_['eta'] = result.x[idx]
            
        self.history_.append({
            'success': result.success,
            'fun': result.fun,
            'nit': result.nit,
            'message': result.message
        })
        
        return self
    
    def predict(
        self,
        S: Union[np.ndarray, pd.Series],
        D: Union[np.ndarray, pd.Series],
        T: Union[np.ndarray, pd.Series]
    ) -> np.ndarray:
        """
        Predict target values using fitted model.
        
        Parameters
        ----------
        S, D, T : array-like
            Surface, Depth, Time values
            
        Returns
        -------
        ndarray
            Predicted Σ values
        """
        S = np.asarray(S, dtype=float)
        D = np.asarray(D, dtype=float)
        T = np.asarray(T, dtype=float)
        return self.trinity_formula(S, D, T)
    
    def score(
        self,
        S: Union[np.ndarray, pd.Series],
        D: Union[np.ndarray, pd.Series],
        T: Union[np.ndarray, pd.Series],
        target: Union[np.ndarray, pd.Series]
    ) -> float:
        """
        Compute R² score.
        
        Returns
        -------
        float
            R² coefficient of determination
        """
        pred = self.predict(S, D, T)
        return r2_score(target, pred)
    
    def invariance_test(
        self,
        S: Union[np.ndarray, pd.Series],
        D: Union[np.ndarray, pd.Series],
        T: Union[np.ndarray, pd.Series],
        target: Union[np.ndarray, pd.Series]
    ) -> Dict[str, Union[float, bool]]:
        """
        Statistical test that η ≠ 0 (triple term required).
        
        Fits three models: linear only, +interactions, +triple.
        Compares R² and tests significance of η.
        
        Parameters
        ----------
        S, D, T, target : array-like
            Data for testing
            
        Returns
        -------
        dict
            Test results with keys:
            - 'r2_linear': R² without interactions
            - 'r2_interactions': R² with pairwise only
            - 'r2_triple': R² with triple term
            - 'eta': Fitted eta coefficient
            - 'eta_std': Standard error of eta (approximate)
            - 't_stat': t-statistic for eta ≠ 0
            - 'p_value': p-value for eta ≠ 0
            - 'invariant_holds': bool, True if eta significantly non-zero
        """
        S = np.asarray(S, dtype=float)
        D = np.asarray(D, dtype=float)
        T = np.asarray(T, dtype=float)
        target = np.asarray(target, dtype=float)
        
        # Fit linear only
        model_linear = TrinityModel(fit_interactions=False, fit_triple=False)
        model_linear.fit(S, D, T, target)
        r2_linear = model_linear.score(S, D, T, target)
        
        # Fit with interactions
        model_int = TrinityModel(fit_interactions=True, fit_triple=False)
        model_int.fit(S, D, T, target)
        r2_int = model_int.score(S, D, T, target)
        
        # Fit with triple
        model_full = TrinityModel(fit_interactions=True, fit_triple=True)
        model_full.fit(S, D, T, target)
        r2_full = model_full.score(S, D, T, target)
        
        eta = model_full.coefficients_.get('eta', 0)
        
        # Approximate standard error via bootstrap
        n_bootstrap = 100
        eta_bootstrap = []
        n_samples = len(S)
        
        for _ in range(n_bootstrap):
            idx = np.random.choice(n_samples, n_samples, replace=True)
            model_boot = TrinityModel(fit_interactions=True, fit_triple=True)
            try:
                model_boot.fit(S[idx], D[idx], T[idx], target[idx])
                eta_bootstrap.append(model_boot.coefficients_.get('eta', 0))
            except:
                pass
                
        eta_std = np.std(eta_bootstrap) if eta_bootstrap else 0.1
        
        # t-test
        if eta_std > 0:
            t_stat = eta / eta_std
            from scipy.stats import t as t_dist
            p_value = 2 * (1 - t_dist.cdf(abs(t_stat), df=n_samples - 7))
        else:
            t_stat = float('inf')
            p_value = 0.0
            
        return {
            'r2_linear': r2_linear,
            'r2_interactions': r2_int,
            'r2_triple': r2_full,
            'eta': eta,
            'eta_std': eta_std,
            't_stat': t_stat,
            'p_value': p_value,
            'invariant_holds': p_value < 0.05 and abs(eta) > 1e-6
        }
    
    def find_critical_surface(
        self,
        S: Union[float, np.ndarray],
        D: Union[float, np.ndarray],
        threshold: float,
        T_range: Tuple[float, float] = (0.001, 1000),
        n_points: int = 1000
    ) -> Dict[str, Union[float, np.ndarray]]:
        """
        Find T values where Σ crosses threshold for given (S,D).
        
        Solves: Σ(S, D, T) = threshold for T
        
        Parameters
        ----------
        S, D : float or array-like
            Surface and Depth values
        threshold : float
            Critical Σ value
        T_range : tuple
            Range to search for T
        n_points : int
            Number of points for root finding
            
        Returns
        -------
        dict
            Critical T values and status
        """
        if isinstance(S, (int, float)):
            S = np.array([S])
            D = np.array([D])
            
        S = np.asarray(S)
        D = np.asarray(D)
        
        results = []
        
        for s, d in zip(S, D):
            # Scan T range
            T_scan = np.linspace(T_range[0], T_range[1], n_points)
            Sigma_scan = self.trinity_formula(s, d, T_scan)
            
            # Find crossings
            diff = Sigma_scan - threshold
            crossings = np.where(np.diff(np.sign(diff)))[0]
            
            if len(crossings) > 0:
                # Linear interpolation for precise root
                idx = crossings[0]
                T1, T2 = T_scan[idx], T_scan[idx + 1]
                S1, S2 = Sigma_scan[idx], Sigma_scan[idx + 1]
                T_crit = T1 + (T2 - T1) * (threshold - S1) / (S2 - S1)
                status = 'crossing_found'
            else:
                T_crit = np.nan
                status = 'no_crossing' if Sigma_scan[0] > threshold else 'always_below'
                
            results.append({
                'S': s,
                'D': d,
                'threshold': threshold,
                'T_critical': T_crit,
                'status': status,
                'Sigma_at_Tmin': Sigma_scan[0],
                'Sigma_at_Tmax': Sigma_scan[-1]
            })
            
        if len(results) == 1:
            return results[0]
        return {'multiple': results}
    
    def get_params(self, deep=True):
        """Get parameters for sklearn compatibility."""
        return {
            'fit_interactions': self.fit_interactions,
            'fit_triple': self.fit_triple,
            'method': self.method,
            'max_iter': self.max_iter
        }
    
    def set_params(self, **params):
        """Set parameters for sklearn compatibility."""
        for key, value in params.items():
            setattr(self, key, value)
        return self


# Convenience alias
Model = TrinityModel
