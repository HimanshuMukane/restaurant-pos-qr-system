FROM mcr.microsoft.com/dotnet/sdk:9.0 AS build
WORKDIR /src

COPY ["apps/backend/NodedrRestaurant.Api.csproj", "apps/backend/"]
RUN dotnet restore "apps/backend/NodedrRestaurant.Api.csproj"

COPY apps/backend/ apps/backend/
WORKDIR "/src/apps/backend"
RUN dotnet publish "NodedrRestaurant.Api.csproj" -c Release -o /app/publish /p:UseAppHost=false

FROM mcr.microsoft.com/dotnet/aspnet:9.0-alpine AS final
WORKDIR /app
EXPOSE 4000
ENV ASPNETCORE_URLS=http://+:4000
COPY --from=build /app/publish .
ENTRYPOINT ["dotnet", "NodedrRestaurant.Api.dll"]
