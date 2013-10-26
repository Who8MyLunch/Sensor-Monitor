
from __future__ import division, print_function, unicode_literals

import numpy as np


def mvn_ll(x, mu, cov):
    """Evaluate log-likelihood of multivariate-normal distribution.

    Based on: http://en.wikipedia.org/wiki/Multivariate_normal,
              http://jonathantemplin.com/files/multivariate/mv11icpsr/mv11icpsr_lecture04.pdf

    Parameters
    ----------
    x : Observation vector (P,), or set of vectors, (N, P)

    mu : Mean vector, (P,)

    cov : covariance square matrrix, (P, P)

    """
    # Setup.
    x = np.asarray(x)
    mu = np.asarray(mu)
    cov = np.asarray(cov)

    # Dimensions.
    if x.ndim == 1:
        N = 1
        P = x.size
        x.shape = N, P
    elif x.ndim == 2:
        N, P = x.shape
    else:
        raise ValueError('Invalid data shape.')

    if mu.size != P:
        raise ValueError('Size of mu must match observation: {:s}'.format(mu.size))

    if cov.ndim != 2:
        raise ValueError('Covariance matrix must be 2D.')

    if not (cov.shape[0] == P and cov.shape[0] == cov.shape[1]):
        raise ValueError('Covariance matrix must be square with size matching observation.')

    # Compute stuff about covariance matrix.
    det = np.linalg.det(cov)
    cov_inv = np.linalg.inv(cov)

    # Build the parts.
    part_1 = 0.5*N*P*np.log(2.*np.pi)

    part_2 = 0.5*N*np.log(det)

    part_3 = [(x[i] - mu).T.dot(cov_inv).dot(x[i] - mu) for i in range(N)]

    # Put it together, flip sign so output is positive quantity.
    log_likelihood = part_1 + part_2 + 0.5*np.sum(part_3)

    return log_likelihood

#################################################


if __name__ == '__main__':
    # Covariance matrix
    # cov = np.asarray([[2.3,   0.1,  0.01, 0.001],
    #                   [0.1,   1.5,  0.1,  0.01],
    #                   [0.01,  0.1,  1.7,  0.1],
    #                   [0.001, 0.01, 0.1,  2.0]])
    cov = np.identity(4)

    # Mean vector
    # mu = np.asarray([2.0, 3.0, 8.0, 10.])
    mu = np.asarray([0.0, 0.0, 0.0, 0.0])

    # Observation.
    x = np.asarray([0, 0, 0, 0.])

    # Evaluate.
    ll = mvn_ll(x, mu, cov)

    print(ll)
