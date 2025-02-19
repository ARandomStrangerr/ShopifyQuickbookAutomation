FROM debian:stable-slim

RUN apt-get update # update system
RUN apt install -y postgresql # install postgres
RUN apt install -y nano # install nano
RUN apt install -y sudo # install sudo

#RUN adduser postgres | echo("user postgres already exist") 
RUN mkdir -p /home/postgres/data # make directory to store the postgres
RUN mkdir -p /home/postgres/work-station # make directory to mount
RUN chown -R postgres:postgres /home/postgres # give postgres user and group control the folder
# create symlink so easier to call
RUN ln -s /usr/lib/postgresql/15/bin/postgres /usr/bin/postgres
#RUN ln -s /usr/lib/postgresql/15/bin/psql /usr/bin/psql | echo ("psql symlink is already exist")
# switch user
USER postgres

# init the db
RUN /usr/lib/postgresql/15/bin/initdb -D /home/postgres/data

# expose the port so that we can connect to it
EXPOSE 5432

#CMD ["/usr/lib/postgresql/15/bin/postgres", "-D", "/home/postgres/data"]
CMD ["bash"]
