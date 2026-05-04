def ode_system(self, X, t):
        # define the forcing function equation for the linear ramp
        if t < self.model.tramp:
            y = self.model.ymag * (t / self.model.tramp)
        else:
            y = self.model.ymag

        x1 = X[0]     # car position in vertical direction
        x1dot = X[1]  # car velocity  in vertical direction
        x2 = X[2]     # wheel position in vertical direction
        x2dot = X[3]  # wheel velocity in vertical direction

        # write the non-trivial equations in vertical direction
        x1ddot = (-self.model.k1 * (x1 - x2) - self.model.c1 * (x1dot - x2dot)) / self.model.m1
        x2ddot = (self.model.k1 * (x1 - x2) + self.model.c1 * (x1dot - x2dot) - self.model.k2 * (x2 - y)) / self.model.m2

        # return the derivatives of the input state vector
        return [x1dot, x1ddot, x2dot, x2ddot]