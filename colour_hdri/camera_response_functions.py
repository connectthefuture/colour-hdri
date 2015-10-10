#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, unicode_literals

import numpy as np

from colour import tstack

from colour_hdri.weighting_functions import weighting_function_Debevec1997


def samples_Grossberg(image_stack, samples=1000, n=256):
    channels_c = None

    cdf_i = []
    for image in image_stack:
        if channels_c is None:
            channels_c = image.pixel_data.shape[-1]

        histograms = tstack(
            [np.histogram(image.pixel_data[..., c], n, range=(0, 1))[0]
             for c in np.arange(channels_c)])
        cdf = np.cumsum(histograms, axis=0)
        cdf_i.append(cdf.astype(float) / np.max(cdf))

    samples_o = np.zeros((samples, channels_c, len(cdf_i)))
    samples_u = np.linspace(0, 1, samples)
    for i in np.arange(samples):
        for j in np.arange(channels_c):
            for k in np.arange(len(cdf_i)):
                samples_o[i, j, k] = (np.argmin(np.abs(cdf_i[k][:, j] -
                                                       samples_u[i])) - 1)

    return samples_o


def g_solve(Z, B, l, w=weighting_function_Debevec1997, n=256):
    # Domain: [0, 255]
    Z = np.asarray(Z).astype(int)
    B = np.asarray(B)
    l = np.asarray(l)

    Z_x, Z_y = Z.shape

    A = np.zeros((Z_x * Z_y + n + 1, n + Z_x))
    b = np.zeros((A.shape[0], 1))
    w = w(np.linspace(0, 1, n))

    k = 0
    for i in np.arange(Z_x):
        for j in np.arange(Z_y):
            w_ij = w[Z[i, j]]
            A[k, Z[i, j]] = w_ij
            A[k, n + i] = -w_ij
            b[k] = w_ij * B[j]
            k += 1

    A[k, n / 2] = 1
    k += 1

    for i in np.arange(n - 2):
        A[k, i] = l * w[i + 1]
        A[k, i + 1] = -2 * l * w[i + 1]
        A[k, i + 2] = l * w[i + 1]
        k += 1

    x = np.linalg.lstsq(A, b)[0]

    g = x[0:n]
    lE = x[n:x.shape[0]]

    return g, lE