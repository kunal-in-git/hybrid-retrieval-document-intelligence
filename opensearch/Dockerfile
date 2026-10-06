FROM opensearchproject/opensearch:3.8.0

USER root

COPY zscaler-root-ca.pem /tmp/zscaler-root-ca.pem

RUN keytool -importcert \
    -noprompt \
    -trustcacerts \
    -alias zscaler-root-ca \
    -file /tmp/zscaler-root-ca.pem \
    -cacerts \
    -storepass changeit \
    && rm /tmp/zscaler-root-ca.pem

USER opensearch