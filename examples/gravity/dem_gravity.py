import click
import time

from simphony.engine import liggghts
from simphony.core.cuba import CUBA


@click.command()
@click.option('--show/--no-show', default=False)
def gravity_example(show):

    runstart = time.time()

    # Read initial particle information from external file
    particles_list = liggghts.read_data_file("gravity_input.dat")

    # configure dem-wrapper
    dem = liggghts.LiggghtsWrapper(use_internal_interface=True)

    # Add particle data to wrapper
    dem.add_dataset(particles_list[0])
    dem.add_dataset(particles_list[1])

    # Re-extract particle container from wrapper
    pc_fall = dem.get_dataset(particles_list[0].name)
    pc_wall = dem.get_dataset(particles_list[1].name)

    # Add time parameters to wrapper
    dem.CM[CUBA.NUMBER_OF_TIME_STEPS] = 5000
    dem.CM[CUBA.TIME_STEP] = 0.00005
    total_steps = 200000

    # Provide boundary condition information
    dem.BC_extension[liggghts.CUBAExtension.BOX_FACES] = ["periodic",
                                                          "fixed",
                                                          "periodic"]

    # Information about fixed walls: 0: No fixation, 1: Particles are fixed
    # falling particles not fixed, wall particles fixed
    dem.BC_extension[liggghts.CUBAExtension.FIXED_GROUP] = [0, 1]

    # Setting material properties
    dem.SP[CUBA.YOUNG_MODULUS] = [1.e4, 1e4]
    dem.SP[CUBA.POISSON_RATIO] = [0.45, 0.45]
    dem.SP[CUBA.RESTITUTION_COEFFICIENT] = [0.85, 0.75, 0.75, 1.0]
    dem.SP[CUBA.FRICTION_COEFFICIENT] = [0.1, 0.2, 0.2, 0.0]
    dem.SP[CUBA.COHESION_ENERGY_DENSITY] = [500.0, 0.0, 0.0, 0.0]

    # Definition of the force type acting between two particles
    # (default: repulsion)
    dem.SP_extension[liggghts.CUBAExtension.PAIR_POTENTIALS] =\
        ['repulsion', 'cohesion']

    # Fix wall particles
    for par in pc_wall.iter_particles():
        par.data[CUBA.VELOCITY] = tuple([0.0, 0.0, 0.0])
        pc_wall.update_particles([par])

    # Adapt properties of mobile particles
    for par in pc_fall.iter_particles():
        # Particle mass modification
        dens = 2.0
        par.data[CUBA.DENSITY] = dens
        
                
        rad = par.data[CUBA.RADIUS]
        par.data[CUBA.MASS] = rad * rad * rad * 4.0 / 3.0 * 3.141592654 * dens
        
        pc_fall.update_particles([par])

        # External force field (gravity)
        F_grav = -par.data[CUBA.MASS]*9.81
        par.data[CUBA.EXTERNAL_APPLIED_FORCE] = tuple([0.0, F_grav, 0.0])

        # Particle velocity modification
        # v_partyx = 0.1
        # par.data[CUBA.VELOCITY] = tuple([v_partx, 0.0, 0.0])

        pc_fall.update_particles([par])

    # Visualisation of the initial state
    if show:
        from simphony.visualisation import aviz

        #  set the proper view parameters for the snapshot
        aviz.show(pc_fall)

    # Main Loop
    step = 0
    for run_number in range(0, total_steps/dem.CM[CUBA.NUMBER_OF_TIME_STEPS]):
        step = step + dem.CM[CUBA.NUMBER_OF_TIME_STEPS]
        print ("running step {} of {}".format(step, total_steps))

        # running the simulation prducing a liggghts dump file called
        # test.traj for visualization
        dem.run()

        if show:
            aviz.snapshot(pc_fall, "gravity{:0>5}.png".format(step))

    # Compute total run time
    runend = time.time()

    print "\ntotal time needed", runend - runstart


if __name__ == '__main__':
    gravity_example()
