import click
import time

from simphony.engine import liggghts
from simphony.core.cuba import CUBA


@click.command()
@click.option('--show/--no-show', default=False)
def billiards_example(show):

    runstart = time.time()

    # Read initial particle information from external file
    particles_list = liggghts.read_data_file("billiards_init.data")

    # configure dem-wrapper
    dem = liggghts.LiggghtsWrapper(use_internal_interface=True)

    # Add particle data to wrapper
    dem.add_dataset(particles_list[0])

    # Re-extract particle container from wrapper
    pc_bill = dem.get_dataset(particles_list[0].name)

    # Add time parameters to wrapper
    dem.CM[CUBA.NUMBER_OF_TIME_STEPS] = 2000
    dem.CM[CUBA.TIME_STEP] = 0.005
    total_steps = 200000

    # Provide boundary condition information
    dem.BC_extension[liggghts.CUBAExtension.BOX_FACES] = ["fixed",
                                                          "fixed",
                                                          "fixed"]

    # Information about fixed walls: 0: No fixation, 1: Particles are fixed
    dem.BC_extension[liggghts.CUBAExtension.FIXED_GROUP] = [0]

    # Setting material properties
    dem.SP[CUBA.YOUNG_MODULUS] = [200.0]
    dem.SP[CUBA.POISSON_RATIO] = [0.45]
    dem.SP[CUBA.RESTITUTION_COEFFICIENT] = [0.75]
    dem.SP[CUBA.FRICTION_COEFFICIENT] = [0.3]

    # Definition of the force type acting between two particles
    # (default: repulsion)
    dem.SP_extension[liggghts.CUBAExtension.PAIR_POTENTIALS] = ['repulsion']

    # Setting the velocity of the break shot ball
    for par in pc_bill.iter_particles():
        if par.coordinates[0] < 0:
            par.data[CUBA.VELOCITY] = tuple([0.5, 0.0, 0.0])
            pc_bill.update_particles([par])

    # Visualisation of the initial state
    if show:
        from simphony.visualisation import aviz

        #  set the proper view parameters for the snapshot
        aviz.show(pc_bill)

    step = 0
    for run_number in range(0, total_steps/dem.CM[CUBA.NUMBER_OF_TIME_STEPS]):
        step = step + dem.CM[CUBA.NUMBER_OF_TIME_STEPS]
        print ("running step {} of {}".format(step, total_steps))

        # running the simulation prducing a liggghts dump file called
        # test.traj for visualization
        dem.run()

        if show:
            aviz.snapshot(pc_bill,
                          "billiards{:0>5}.png".format(step))

    # Compute total run time
    runend = time.time()

    print "\ntotal time needed", runend - runstart


if __name__ == '__main__':
    billiards_example()
