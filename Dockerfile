From simphony/simphony-lammps

RUN git clone https://github.com/simphony/simphony-liggghts.git \
    && cd simphony-liggghts \
    && ./install_external.sh

RUN cd simphony-liggghts \
    && python setup.py install \
    && cd .. \
    && rm -rf simphony-liggghts \
    && apt-get autoremove -yq \
    && apt-get clean -yq \
    && rm -rf /var/lib/apt/lists/*
