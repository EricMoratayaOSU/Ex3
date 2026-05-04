def calculate(self, doCalc=True):
        #Step 1.  Read from the widgets
        self.model.m1 = float(self.le_m1.text())
        self.model.m2 = float(self.le_m2.text())
        self.model.c1 = float(self.le_c1.text())
        self.model.k1 = float(self.le_k1.text())
        self.model.k2 = float(self.le_k2.text())
        self.model.v = float(self.le_v.text())

        #recalculate min and max k values
        g = 9.81
        W1 = self.model.m1 * g
        W_total = (self.model.m1 + self.model.m2) * g
        
        self.model.mink1 = W1 / (6.0 * 0.0254)
        self.model.maxk1 = W1 / (3.0 * 0.0254)
        self.model.mink2 = W_total / (1.5 * 0.0254)
        self.model.maxk2 = W_total / (0.75 * 0.0254)