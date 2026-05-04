import statistics
from Polymer import macroMolecule

def main():
    # Command Line Interface (CLI) Inputs
    n_input = input("degree of polymerization (1000)?: ")
    target_N = int(n_input) if n_input.strip() else 1000

    m_input = input("How many molecules (50)?: ")
    num_molecules = int(m_input) if m_input.strip() else 50

    # Run Simulation
    molecules = []
    for _ in range(num_molecules):
        # Instantiate with the target_N (Polymer.py handles the normal distribution)
        poly = macroMolecule(degreeOfPolymerization=target_N)
        poly.freelyJointedChainModel()
        molecules.append(poly)

    # Gather Data
    com_x, com_y, com_z = 0.0, 0.0, 0.0
    e2e_list = []
    rg_list = []
    mw_list = []

    for poly in molecules:
        # Summing center of mass coordinates
        com_x += poly.centerOfMass.x
        com_y += poly.centerOfMass.y
        com_z += poly.centerOfMass.z
        
        # Collect distances (converting meters to micrometers as requested)
        e2e_list.append(poly.endToEndDistance * 1e6)
        rg_list.append(poly.radiusOfGyration * 1e6)
        
        # Collect Molecular Weights for PDI calculation
        mw_list.append(poly.MW)

    # Statistical Calculation
    # Average Center of Mass (Convert meters to nanometers)
    avg_com_x = (com_x / num_molecules) * 1e9
    avg_com_y = (com_y / num_molecules) * 1e9
    avg_com_z = (com_z / num_molecules) * 1e9

    # End-to-end distance stats
    avg_e2e = statistics.mean(e2e_list)
    std_e2e = statistics.stdev(e2e_list) if num_molecules > 1 else 0.0

    # Radius of gyration stats
    avg_rg = statistics.mean(rg_list)
    std_rg = statistics.stdev(rg_list) if num_molecules > 1 else 0.0

    # Calculate Polydispersity Index (PDI)
    # PDI = Mw / Mn (Weight average MW / Number average MW)
    Mn = sum(mw_list) / len(mw_list)
    Mw = sum(mw**2 for mw in mw_list) / sum(mw_list)
    pdi = Mw / Mn

    # Display Output
    print(f"\nMetrics for {num_molecules} molecules of degree of polymerization = {target_N}")
    print(f"Avg. Center of Mass (nm) = {avg_com_x:.3f}, {avg_com_y:.3f}, {avg_com_z:.3f}")
    print("End-to-end distance (um):")
    print(f"Average = {avg_e2e:.3f}")
    print(f"Std. Dev. = {std_e2e:.3f}")
    print("Radius of gyration (um):")
    print(f"Average = {avg_rg:.3f}")
    print(f"Std. Dev. = {std_rg:.3f}")
    print(f"PDI = {pdi:.2f}")

if __name__ == "__main__":
    main()