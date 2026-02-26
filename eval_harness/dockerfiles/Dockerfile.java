FROM maven:3.9-eclipse-temurin-17

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl procps netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /repo

# Copy generated repo
COPY ./generated_repo /repo

# Pre-download Maven dependencies (speeds up later build)
RUN if [ -f pom.xml ]; then \
        mvn dependency:go-offline -q 2>/dev/null || true; \
    fi

# Fix Java version: ensure Java 17 in pom.xml (some repos have Java 11)
RUN if [ -f pom.xml ]; then \
        sed -i 's|<maven.compiler.source>11</maven.compiler.source>|<maven.compiler.source>17</maven.compiler.source>|g' pom.xml && \
        sed -i 's|<maven.compiler.target>11</maven.compiler.target>|<maven.compiler.target>17</maven.compiler.target>|g' pom.xml && \
        sed -i 's|<source>11</source>|<source>17</source>|g' pom.xml && \
        sed -i 's|<target>11</target>|<target>17</target>|g' pom.xml; \
    fi

# Copy golden oracle tests
# Handle both src/test/ and tests/ structures from golden oracle
COPY ./golden_tests /repo/golden_tests_staging

RUN if [ -d /repo/golden_tests_staging/src/test ]; then \
        rm -rf /repo/src/test && \
        mkdir -p /repo/src && \
        cp -r /repo/golden_tests_staging/src/test /repo/src/test; \
    elif [ -d /repo/golden_tests_staging/tests ]; then \
        mkdir -p /repo/src/test/java && \
        cp -r /repo/golden_tests_staging/tests/* /repo/src/test/java/; \
    fi && \
    rm -rf /repo/golden_tests_staging

# Compile (skip tests -- we will run tests in the entrypoint)
RUN if [ -f pom.xml ]; then \
        mvn clean compile -DskipTests -q 2>/dev/null || true; \
    fi

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/entrypoint.sh"]
