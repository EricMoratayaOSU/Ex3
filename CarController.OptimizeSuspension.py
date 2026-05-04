def OptimizeSuspension(self):
        #Step 1: set parameters based on GUI inputs
        self.calculate(doCalc=False)
        
        #Step 2: make an initial guess for k1, c1, k2
        x0 = np.array([self.model.k1, self.model.c1, self.model.k2])
        
        #Step 3: optimize the suspension using Nelder-Mead 
        answer = minimize(self.SSE, x0, method='Nelder-Mead')
        
        # Extract the optimized values and update the model
        self.model.k1, self.model.c1, self.model.k2 = answer.x
        
        # Update the view with the new optimized parameters
        self.view.updateView(self.model)