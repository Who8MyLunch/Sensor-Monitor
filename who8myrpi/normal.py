
from __future__ import division, print_function, unicode_literals

import numpy as np
import math

# http://en.wikipedia.org/wiki/Multivariate_normal


def norm_pdf_multivariate(x, mu, sigma):
    size = len(x)
    if size == len(mu) and (size, size) == sigma.shape:
        det = np.linalg.det(sigma)
        if det == 0:
            raise NameError("The covariance matrix can't be singular")

        norm_const = 1.0 / (math.pow((2*np.pi), float(size)/2) * math.pow(det, 1.0/2))
        x_mu = x - mu
        inv = sigma.I
        result = math.pow(math.e, -0.5 * (x_mu * inv * x_mu.T))
        return norm_const * result
    else:
        raise NameError("The dimensions of the input don't match")

# covariance matrix
sigma = np.asarray([[2.3, 0, 0, 0],
                    [0, 1.5, 0, 0],
                    [0, 0, 1.7, 0],
                    [0, 0,   0, 2]])
# mean vector
mu = np.asarray([2, 3, 8, 10])

# input
x = np.asarray([2.1, 3.5, 8, 9.5])

print(norm_pdf_multivariate(x, mu, sigma))
