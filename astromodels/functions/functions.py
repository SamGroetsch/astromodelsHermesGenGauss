__author__ = 'giacomov'

import math
import numpy as np
import warnings
from scipy.special import gammaincc, gamma
import exceptions

from astromodels.functions.function import Function
from astromodels.functions.function import FunctionMeta
from astromodels.units import get_units
import astropy.units as astropy_units


class GSLNotAvailable(UserWarning):
    pass


class NaimaNotAvailable(UserWarning):
    pass


class InvalidUsageForFunction(exceptions.Exception):
    pass

# Now let's try and import optional dependencies

try:

    # Naima is for numerical computation of Synch. and Inverse compton spectra in randomly oriented
    # magnetic fields

    import naima
    import astropy.units as u

except ImportError:

    warnings.warn("The naima package is not available. Models that depend on it will not be available",
                  NaimaNotAvailable)

    has_naima = False

else:

    has_naima = True

try:

    # GSL is the GNU Scientific Library. Pygsl is the python wrapper for it. It is used by some
    # functions for faster computation

    from pygsl.testing.sf import gamma_inc

except ImportError:

    warnings.warn("The GSL library or the pygsl wrapper cannot be loaded. Models that depend on it will not be "
                  "available.", GSLNotAvailable)

    has_gsl = False

else:

    has_gsl = True

# noinspection PyPep8Naming
class powerlaw(Function):
    r"""
    description :

        A simple power-law

    latex : $ K~\frac{x}{piv}^{index} $

    parameters :

        K :

            desc : Normalization (differential flux at the pivot value)
            initial value : 1.0

        piv :

            desc : Pivot value
            initial value : 1
            fix : yes

        index :

            desc : Photon index
            initial value : -2
            min : -10
            max : 10

    tests :
        - { x : 10, function value: 0.01, tolerance: 1e-20}
        - { x : 100, function value: 0.0001, tolerance: 1e-20}

    """

    __metaclass__ = FunctionMeta

    def _set_units(self, x_unit, y_unit):

        # The index is always dimensionless
        self.index.unit = astropy_units.dimensionless_unscaled

        # The pivot energy has always the same dimension as the x variable
        self.piv.unit = x_unit

        # The normalization has the same units as the y

        self.K.unit = y_unit

    # noinspection PyPep8Naming
    def evaluate(self, x, K, piv, index):

        return K * np.power(x / piv, index)

# noinspection PyPep8Naming
class powerlaw_flux(Function):
        r"""
        description :

            A simple power-law with the photon flux in a band used as normalization. This will reduce the correlation
            between the index and the normalization.

        latex : $ \frac{F(\gamma+1)} {b^{\gamma+1} - a^{\gamma+1}} (x)^{\gamma}$

        parameters :

            F :

                desc : Integral between a and b
                initial value : 1

            index :

                desc : Photon index
                initial value : -2
                min : -10
                max : 10

            a :

                desc : lower bound for the band in which computing the integral F
                initial value : 1.0
                fix : yes

            b :

                desc : upper bound for the band in which computing the integral F
                initial value : 100.0
                fix : yes

        """

        __metaclass__ = FunctionMeta

        def _set_units(self, x_unit, y_unit):

            # The flux is the integral over x, so:
            self.F.unit = y_unit * x_unit

            # The index is always dimensionless
            self.index.unit = astropy_units.dimensionless_unscaled

            # a and b have the same units as x

            self.a.unit = x_unit
            self.b.unit = x_unit

        # noinspection PyPep8Naming
        def evaluate(self, x, F, index, a, b):

            gp1 = index + 1

            return F * gp1 / (b**gp1 - a**gp1) * np.power(x, index)

class broken_powerlaw(Function):
    r"""
    description :

        A broken power law function

    latex : $ f(x)= K~\begin{cases}\left( \frac{x}{x_{b}} \right)^{\alpha} & x < x_{b} \\ \left( \frac{x}{x_{b}} \right)^{\beta} & x \ge x_{b} \end{cases} $

    parameters :

        K :

            desc : Normalization (differential flux at x_b)
            initial value : 1.0

        xb :

            desc : Break point
            initial value : 10
            min : 1.0

        alpha :

            desc : Index before the break xb
            initial value : -1.5
            min : -10
            max : 10

        beta :

            desc : Index after the break xb
            initial value : -2.5
            min : -10
            max : 10

    """

    __metaclass__ = FunctionMeta

    def _set_units(self, x_unit, y_unit):

        # The normalization has the same units as y
        self.K.unit = y_unit

        # The break point has always the same dimension as the x variable
        self.xb.unit = x_unit

        # alpha and beta are dimensionless
        self.alpha.unit = astropy_units.dimensionless_unscaled
        self.beta.unit = astropy_units.dimensionless_unscaled

    # noinspection PyPep8Naming
    def evaluate(self, x, K, xb, alpha, beta):

        return K * np.where((x < xb), np.power(x,alpha), np.power(x,beta))

# noinspection PyPep8Naming
class gaussian(Function):
    r"""
    description :

        A Gaussian function

    latex : $ K \frac{1}{\sigma \sqrt{2 \pi}}\exp{\frac{(x-\mu)^2}{2~(\sigma)^2}} $

    parameters :

        F :

            desc : Integral between -inf and +inf. Fix this to 1 to obtain a Normal distribution
            initial value : 1

        mu :

            desc : Central value
            initial value : 0.0

        sigma :

            desc : standard deviation
            initial value : 1.0
            min : 1e-12

    tests :
        - { x : 0.0, function value: 0.3989422804014327, tolerance: 1e-10}
        - { x : -1.0, function value: 0.24197072451914337, tolerance: 1e-9}

    """

    __metaclass__ = FunctionMeta

    # Place this here to avoid recomputing it all the time

    __norm_const = 1.0 / (math.sqrt(2 * np.pi))

    def _set_units(self, x_unit, y_unit):

        # The normalization is the integral from -inf to +inf, i.e., has dimensions of
        # y_unit * x_unit
        self.F.unit = y_unit * x_unit

        # The mu has the same dimensions as the x
        self.mu.unit = x_unit

        # sigma has the same dimensions as x
        self.sigma.unit = x_unit

    # noinspection PyPep8Naming
    def evaluate(self, x, F, mu, sigma):

        norm = self.__norm_const / sigma

        return F * norm * np.exp(-np.power(x - mu, 2.) / (2 * np.power(sigma, 2.)))


class uniform_prior(Function):
    r"""
    description :

        A function which is constant on the interval lower_bound - upper_bound and 0 outside the interval. The
        extremes of the interval are counted as part of the interval.

    latex : $ f(x)=\begin{cases}0 & x < \text{lower_bound} \\\text{value} & \text{lower_bound} \le x \le \text{upper_bound} \\ 0 & x > \text{upper_bound} \end{cases}$

    parameters :

        lower_bound :

            desc : Lower bound for the interval
            initial value : 0

        upper_bound :

            desc : Upper bound for the interval
            initial value : 1

        value :

            desc : Value in the interval
            initial value : 1.0

    tests :
        - { x : 0.5, function value: 1.0, tolerance: 1e-20}
        - { x : -0.5, function value: 0, tolerance: 1e-20}

    """

    __metaclass__ = FunctionMeta

    def _set_units(self, x_unit, y_unit):

        # Lower and upper bound has the same unit as x
        self.lower_bound.unit = x_unit
        self.upper_bound.unit = x_unit

        # value has the same unit as y
        self.value.unit = y_unit

    def evaluate(self, x, lower_bound, upper_bound, value):

        return np.where( (x >= lower_bound) & (x <= upper_bound), value, 0.0)


class log_uniform_prior(Function):
    r"""
    description :

        A function which is 1/x on the interval lower_bound - upper_bound and 0 outside the interval. The
        extremes of the interval are NOT counted as part of the interval. Lower_bound must be >= 0.

    latex : $ f(x)=\begin{cases}0 & x \le \text{lower_bound} \\\frac{1}{x} & \text{lower_bound} < x < \text{upper_bound} \\ 0 & x \ge \text{upper_bound} \end{cases}$

    parameters :

        lower_bound :

            desc : Lower bound for the interval
            initial value : 0
            min : 0

        upper_bound :

            desc : Upper bound for the interval
            initial value : 100

    tests :
        - { x : 50, function value: (1.0 / 50.0), tolerance: 1e-20}
        - { x : 200, function value: 0, tolerance: 1e-20}

    """

    __metaclass__ = FunctionMeta

    def _set_units(self, x_unit, y_unit):

        # Lower and upper bound has the same unit as x
        self.lower_bound.unit = x_unit
        self.upper_bound.unit = x_unit

    def evaluate(self, x, lower_bound, upper_bound):

        return np.where((x > lower_bound) & (x < upper_bound), 1.0/x, 0.0)


# noinspection PyPep8Naming
class sin(Function):
    r"""
    description :

        A sinusodial function

    latex : $ K~\sin{(2\pi f x + \phi)} $

    parameters :

        K :

            desc : Normalization
            initial value : 1

        f :

            desc : frequency
            initial value : 1.0 / (2 * np.pi)
            min : 0

        phi :

            desc : phase
            initial value : 0
            min : -np.pi
            max : +np.pi
            unit: rad

    tests :
        - { x : 0.0, function value: 0.0, tolerance: 1e-10}
        - { x : 1.5707963267948966, function value: 1.0, tolerance: 1e-10}

    """

    __metaclass__ = FunctionMeta

    def _set_units(self, x_unit, y_unit):

        # The normalization has the same unit of y
        self.K.unit = y_unit

        # The unit of f is 1 / [x] because fx must be a pure number
        self.f.unit = x_unit**(-1)

        # The unit of phi is always the same (radians)

        self.phi.unit = astropy_units.rad

    # noinspection PyPep8Naming
    def evaluate(self, x, K, f, phi):

        return K * np.sin(2 * np.pi * f * x + phi)


if has_naima:

    class synchrotron(Function):
        r"""
        description :

            Synchrotron spectrum from an input particle distribution, using Naima (naima.readthedocs.org)

        latex: not available

        parameters :

            B :

                desc : magnetic field
                initial value : 3.24e-6
                unit: Gauss

            distance :

                desc : distance of the source
                initial value : 1.0
                unit : kpc

            emin :

                desc : minimum energy for the particle distribution
                initial value : 1
                fix : yes
                unit: GeV

            emax :
                desc : maximum energy for the particle distribution
                initial value : 510e3
                fix : yes
                unit: GeV

            need:

                desc: number of points per decade in which to evaluate the function
                initial value : 10
                min : 2
                max : 100
                fix : yes

        """

        __metaclass__ = FunctionMeta

        def _set_units(self, x_unit, y_unit):

            # This function can only be used as a spectrum,
            # so let's check that x_unit is a energy and y_unit is
            # differential flux

            if hasattr(x_unit,"physical_type") and x_unit.physical_type == 'energy':

                # Now check that y is a differential flux
                current_units = get_units()
                should_be_unitless = y_unit * (current_units.photon_energy * current_units.time * current_units.area)

                if not hasattr(should_be_unitless,'physical_type') or \
                   should_be_unitless.decompose().physical_type != 'dimensionless':

                    # y is not a differential flux
                    raise InvalidUsageForFunction("Unit for y is not differential flux. The function synchrotron "
                                                  "can only be used as a spectrum.")
            else:

                raise InvalidUsageForFunction("Unit for x is not an energy. The function synchrotron can only be used "
                                              "as a spectrum")

            # we actually don't need to do anything as the units are already set up

        def set_particle_distribution(self, function):

            self._particle_distribution = function

            # Now set the units for the function

            current_units = get_units()

            self._particle_distribution._set_units(current_units.particle_energy, current_units.particle_energy**(-1))

            # Naima wants a function which accepts a quantity as x (in units of eV) and returns an astropy quantity,
            # so we need to create a wrapper which will remove the unit from x and add the unit to the return
            # value

            self._particle_distribution_wrapper = lambda x: function(x.value) / current_units.particle_energy

        def get_particle_distribution(self):

            return self._particle_distribution

        particle_distribution = property(get_particle_distribution, set_particle_distribution,
                                         doc="""Get/set particle distribution for electrons""")

        # noinspection PyPep8Naming
        def evaluate(self, x, B, distance, emin, emax, need):

            _synch = naima.models.Synchrotron(self._particle_distribution_wrapper, B * astropy_units.Gauss,
                                              Eemin = emin * astropy_units.GeV,
                                              Eemax = emax * astropy_units.GeV, nEed = need)

            return _synch.flux(x * get_units().photon_energy, distance=distance * astropy_units.kpc).value

        def to_dict(self, minimal=False):

            data = super(Function, self).to_dict(minimal)

            if not minimal:

                data['extra_setup'] = {'particle_distribution': self.particle_distribution.path}

            return data


class line(Function):
    r"""
    description :

        A linear function

    latex : $ a * x + b $

    parameters :

        a :

            desc : linear coefficient
            initial value : 1

        b :

            desc : intercept
            initial value : 0

    """

    __metaclass__ = FunctionMeta

    def _set_units(self, x_unit, y_unit):

        # a has units of y_unit / x_unit, so that a*x has units of y_unit
        self.a.unit = y_unit / x_unit

        # b has units of y
        self.b.unit = y_unit

    def evaluate(self, x, a, b):

        return a * x + b

class identity(Function):
    r"""
    description :

        Return x

    latex : $ x $

    parameters : {}

    """

    __metaclass__ = FunctionMeta

    def _set_units(self, x_unit, y_unit):

        pass

    def evaluate(self, x):

        return x


class bias(Function):
    r"""
    description :

        Return x plus a bias

    latex : $ x + k$

    parameters :

        k :

            desc : Constant value
            initial value : 0

    """

    __metaclass__ = FunctionMeta

    def _set_units(self, x_unit, y_unit):

        # k has units of x

        self.k.unit = x_unit

        if x_unit != y_unit:

            raise InvalidUsageForFunction("Function bias cannot be given different units for x and y")

    def evaluate(self, x, k):

        return x + k


class band(Function):
    r"""
    description :

        The Band model from Band et al. 1993, implemented however in a way which reduces the covariances between
        the parameters (Calderone et al., MNRAS, 448, 403C, 2015)

    latex : $ \text{(Calderone et al., MNRAS, 448, 403C, 2015)} $

    parameters :

        alpha :
            desc : The index for x smaller than the x peak
            initial value : -1
            min : -10
            max : 10

        beta :

            desc : index for x greater than the x peak (only if opt=1, i.e., for the
                   Band model)
            initial value : -2.2
            min : -7
            max : -1

        xp :

            desc : position of the peak in the x*x*f(x) space (if x is energy, this is the nuFnu or SED space)
            initial value : 200.0
            min : 0

        F :

            desc : integral in the band defined by a and b
            initial value : 1e-6

        a:

            desc : lower limit of the band in which the integral will be computed
            initial value : 1.0
            min : 0
            fix : yes

        b:

            desc : upper limit of the band in which the integral will be computed
            initial value : 10000.0
            min : 0
            fix : yes

        opt :

            desc : option to select the spectral model (0 corresponds to a cutoff power law, 1 to the Band model)
            initial value : 1
            min : 0
            max : 1
            fix : yes

    """

    __metaclass__ = FunctionMeta

    def _set_units(self, x_unit, y_unit):

        # alpha and beta are always unitless

        self.alpha.unit = astropy_units.dimensionless_unscaled
        self.beta.unit = astropy_units.dimensionless_unscaled

        # xp has the same dimension as x
        self.xp.unit = x_unit

        # F is the integral over x, so it has dimensions y_unit * x_unit
        self.F.unit = y_unit * x_unit

        # a and b have the same units of x
        self.a.unit = x_unit
        self.b.unit = x_unit

        # opt is just a flag, and has no units
        self.opt.unit = astropy_units.dimensionless_unscaled

    @staticmethod
    def ggrb_int_cpl( a, Ec, Emin, Emax):

        i1 = gammaincc(2 + a, Emin / Ec) * gamma(2+a)
        i2 = gammaincc(2 + a, Emax / Ec) * gamma(2+a)

        return -Ec * Ec * (i2 - i1)

    @staticmethod
    def ggrb_int_pl(a, b, Ec, Emin, Emax):

        pre = pow(a-b, a-b) * math.exp(b-a) / pow(Ec, b)

        if b != -2:

            return pre / (2+b) * (pow(Emax, 2+b) - pow(Emin, 2+b))

        else:

            return pre * math.log(Emax / Emin)

    def evaluate(self, x, alpha, beta, xp, F, a, b, opt):

        assert opt == 0 or opt == 1, "Opt must be either 0 or 1"

        # Cutoff energy

        if alpha == -2:

            Ec = xp / 0.0001 #TRICK: avoid a=-2

        else:

            Ec = xp / (2 + alpha)

        # Split energy

        Esplit = (alpha-beta) * Ec

        # Evaluate model integrated flux and normalization

        if opt==0:

            # Cutoff power law

            intflux = self.ggrb_int_cpl(alpha, Ec, a, b)

        else:

            # Band model

            if a <= Esplit and Esplit <= b:

                intflux = (self.ggrb_int_cpl(alpha, Ec, a, Esplit) +
                           self.ggrb_int_pl (alpha, beta, Ec, Esplit, b))

            else:

                if Esplit < a:

                    intflux = self.ggrb_int_pl(alpha, beta, Ec, a, b)

                else:

                    raise RuntimeError("Esplit > emax!")

        erg2keV = 6.24151e8

        norm = F * erg2keV / intflux

        if opt==0:

            # Cutoff power law

            flux = norm * np.power(x / Ec, alpha) * np.exp( - x / Ec)

        else:

            idx = (x < Esplit)

            flux = np.zeros_like( x )

            flux[idx] = ( norm * np.power(x[idx] / Ec, alpha) *
                          np.exp(-x[idx] / Ec) )

            nidx = ~idx

            flux[nidx] = ( norm * pow(alpha-beta, alpha-beta) * math.exp(beta-alpha) *
                           np.power(x[nidx] / Ec, beta) )

        return flux


class log_parabola(Function):
    r"""
    description :

        A log-parabolic function

    latex : $ K \left( \frac{x}{piv} \right)^{\alpha -\beta \log{\left( \frac{x}{piv} \right)}} $

    parameters :

        K :

            desc : Normalization
            initial value : 0

        piv :
            desc : Pivot (keep this fixed)
            initial value : 1
            fix : yes

        alpha :

            desc : index
            initial value : -2.0

        beta :

            desc : curvature
            initial value : 1.0

    """

    __metaclass__ = FunctionMeta

    def _set_units(self, x_unit, y_unit):

        # K has units of y

        self.K.unit = y_unit

        # piv has the same dimension as x
        self.piv.unit = x_unit

        # alpha and beta are dimensionless
        self.alpha.unit = astropy_units.dimensionless_unscaled
        self.beta.unit = astropy_units.dimensionless_unscaled

    def evaluate(self, x, K, piv, alpha, beta):

        xx = x/piv

        return K * xx**(alpha - beta * np.log10(xx))

    @property
    def peak_energy(self):
        """
        Returns the peak energy in the nuFnu spectrum

        :return: peak energy in keV
        """

        # Eq. 6 in Massaro et al. 2004
        # (http://adsabs.harvard.edu/abs/2004A%26A...413..489M)

        return self.piv.value * pow(10, (2 + self.alpha.value) / (2 * self.beta.value) )

if has_gsl:

    class cutoff_powerlaw_flux(Function):
        r"""
            description :

                A cutoff power law having the flux as normalization, which should reduce the correlation among
                parameters.

            latex : $ \frac{F}{T(b)-T(a)} ~x^{\alpha}~\exp{(-x/x_{c})}~\text{with}~T(x)=-x_{c}^{\alpha+1} \Gamma(\alpha+1, x/C)~\text{(}\Gamma\text{ is the incomplete gamma function)} $

            parameters :

                F :

                    desc : Integral between a and b
                    initial value : 1e-5

                alpha :

                    desc : photon index
                    initial value : -2.0

                xc :

                    desc : cutoff position
                    initial value : 50.0

                a :

                    desc : lower bound for the band in which computing the integral F
                    initial value : 1.0
                    fix : yes

                b :

                    desc : upper bound for the band in which computing the integral F
                    initial value : 100.0
                    fix : yes
            """

        __metaclass__ = FunctionMeta

        def _set_units(self, x_unit, y_unit):

            # K has units of y * x
            self.F.unit = y_unit * x_unit

            # alpha is dimensionless
            self.alpha.unit = astropy_units.dimensionless_unscaled

            # xc, a and b have the same dimension as x
            self.xc.unit = x_unit
            self.a.unit = x_unit
            self.b.unit = x_unit

        @staticmethod
        def _integral(a,b, alpha, ec):

            ap1 = alpha + 1

            integrand = lambda x: -pow(ec, ap1) * gamma_inc(ap1, x / ec)

            return integrand(b) - integrand(a)

        def evaluate(self, x, F, alpha, xc, a, b):

            this_integral = self._integral(a, b, alpha, xc)

            return F / this_integral * np.power(x, alpha) * np.exp(-x / xc)