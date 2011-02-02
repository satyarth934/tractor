# make mixture-of-Gaussian galaxy profiles

import matplotlib
matplotlib.use('Agg')
from math import pi as pi
import pylab as plt
import numpy as np
import scipy.optimize as op

# magic number
maxradius = 8.

# note wacky normalization because this is for 2-d Gaussians
# (but only ever called in 1-d).  Wacky!
def not_normal(x, m, V):
    return 1. / (2. * pi * V) * np.exp(-0.5 * x**2 / V)

def hogg_dev(x):
    return np.exp(-1. * (x**0.25))

def mixture_of_not_normals(x, pars):
    K = len(pars)/2
    y = 0.
    for k in range(K):
        y += pars[k] * not_normal(x, 0., pars[k+K])
    return y

# note magic 1e7
# note that you can do (x * ymix - x * ytrue)**2 or (ymix - ytrue)**2
# each has disadvantages.
def badness_of_fit_exp(lnpars):
    pars = np.exp(lnpars)
    x = np.arange(0., maxradius, 0.01)
    return np.mean((mixture_of_not_normals(x, pars)
                    - np.exp(-x))**2) * 1e7

# note magic 1e7
# note that you can do (x * ymix - x * ytrue)**2 or (ymix - ytrue)**2
# each has disadvantages.
def badness_of_fit_dev(lnpars):
    pars = np.exp(lnpars)
    x = np.arange(0., maxradius, 0.001)
    return np.mean((mixture_of_not_normals(x, pars)
                    - hogg_dev(x))**2) * 1e7

def optimize_mixture(K, pars, model):
    if model == 'exp':
        func = badness_of_fit_exp
    if model == 'dev':
        func = badness_of_fit_dev
    newlnpars = op.fmin_bfgs(func, np.log(pars))
    return (func(newlnpars), np.exp(newlnpars))

def plot_mixture(pars, fn, model):
    x1 = np.arange(0., maxradius, 0.001)
    if model == 'exp':
        y1 = np.exp(-x1)
        badness = badness_of_fit_exp(np.log(pars))
    if model == 'dev':
        y1 = hogg_dev(x1)
        badness = badness_of_fit_dev(np.log(pars))
    x2 = np.arange(0., maxradius+2., 0.001)
    y2 = mixture_of_not_normals(x2, pars)
    plt.clf()
    plt.plot(x1, y1, 'k-')
    plt.plot(x2, y2, 'k-', lw=4, alpha=0.5)
    plt.xlim(-0.5, np.max(x2))
    plt.ylim(-0.1*np.max(y1), 1.1*np.max(y1))
    plt.title('K = %d / badness = %f' % (len(pars)/2, badness))
    plt.savefig(fn)

def rearrange_pars(pars):
    K = len(pars) / 2
    indx = np.argsort(pars[K:K+K])
    amp = pars[indx]
    var = pars[K+indx]
    return np.append(amp, var)

if __name__ == '__main__':
    for model in ['exp', 'dev']:
        amp = []
        var = []
        badness = 1.e30
        oldbadness = 0.5 * badness
        for K in range(1,20):
            print 'working on K = %d' % K
            newvar = 0.5 * np.min(np.append(var,1.0))
            newamp = 1.0 * newvar
            amp = np.append(newamp, amp)
            var = np.append(newvar, var)
            pars = np.append(amp, var)
            for i in range(3 * K):
                (badness, pars) = optimize_mixture(K, pars, model)
                if badness < 0.5 * oldbadness:
                    print 'improved enough'
                    oldbadness = badness
                    break
                else:
                    print 'not enough improvement; trying again'
                    var[0] = 0.5 * var[np.random.randint(K)]
                    amp[0] = 1.0 * var[0]
                    pars = np.append(amp, var)
            pars = rearrange_pars(pars)
            plot_mixture(pars, 'K%02d_%s.png' % (K, model), model)
            amp = pars[0:K]
            var = pars[K:K+K]
            # magic number
            if badness < 0.1:
                break
