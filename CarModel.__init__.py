#set default values for the properties of the quarter car model
        self.m1 = 450.0  # mass of car body in kg 
        self.m2 = 20.0   # mass of wheel in kg (from GUI default) [cite: 218, 220]
        self.c1 = 4500.0 # damping coefficient in N*s/m [cite: 197]
        self.k1 = 15000.0 # spring constant of suspension in N/m [cite: 217]
        self.k2 = 90000.0 # spring constant of tire in N/m [cite: 185]
        self.v = 120.0   # velocity of car in kph [cite: 203]

        # Calculate limits based on static compression limits
        g = 9.81
        W1 = self.m1 * g
        W_total = (self.m1 + self.m2) * g
        
        self.mink1 = W1 / (6.0 * 0.0254)  # 6 inches to meters
        self.maxk1 = W1 / (3.0 * 0.0254)  # 3 inches to meters
        self.mink2 = W_total / (1.5 * 0.0254)  # 1.5 inches to meters
        self.maxk2 = W_total / (0.75 * 0.0254) # 0.75 inches to meters
        
        self.accel = None
        self.accelMax = 0.0
        self.accelLim = 2.0  # limit the acceleration to ~2.0g [cite: 109]