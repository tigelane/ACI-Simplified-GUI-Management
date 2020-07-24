FROM python:3.8-alpine

# install ssh client and git
RUN apk add --update --no-cache openssh-client git 

# clone our private repository
RUN git clone https://github.com/tigelane/ACI-Simplified-GUI-Management.git && cd devnet-create-2020

# Clone all the tools for use in the gui
RUN git clone https://github.com/tigelane/aci-legacy-tenant-epg.git devnet-create-2020/repos/dc_2020_aci_legacy_tenant
RUN git clone https://github.com/tigelane/aci-appliance-server.git devnet-create-2020/repos/dc_2020_aci_appliance_server

WORKDIR /devnet-create-2020
RUN pip install -r requirements.txt

EXPOSE 5000
ENV FLASK_APP devnet_create_2020.py
CMD ["flask", "run", "--host", "0.0.0.0"]