FROM maven:3.9.6-eclipse-temurin-21 AS build
WORKDIR /app
COPY pom.xml .
RUN mkdir -p src/main/java/me/andrii.kairo
COPY KairoBot.java src/main/java/me/andrii/kairo/
RUN mvn clean package

FROM eclipse-temurin:21-jre-jammy
WORKDIR /app
COPY --from=build /app/target/kairo-bot-1.0.jar app.jar
ENTRYPOINT ["java", "-jar", "app.jar"]
