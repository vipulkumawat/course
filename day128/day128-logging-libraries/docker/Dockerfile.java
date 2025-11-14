FROM openjdk:17-slim

RUN apt-get update && apt-get install -y maven

WORKDIR /app

COPY java-lib/ ./
COPY examples/JavaDemo.java ./src/main/java/

RUN mvn compile exec:java -Dexec.mainClass="JavaDemo"

CMD ["mvn", "exec:java", "-Dexec.mainClass=JavaDemo"]
