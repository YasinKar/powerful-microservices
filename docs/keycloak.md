# Keycloak Configuration Guide (Docker + PostgreSQL)

This document explains the full configuration flow of **Keycloak** using **Docker Compose** or **Kubernetes**, starting from initial admin setup to creating realms, clients, users, and etc.

---

## Configurations (Environment Variables & Secrets)

If you are using Docker Compose you need to configure and set up the **envs** and if you are using k8s you need to change the **secret component** in the k8s/keycloak/deployment.yml path.

You can update this file in the **keycloak/.env** path:

```env
KEYCLOAK_ADMIN=keycloak
KEYCLOAK_ADMIN_PASSWORD=keycloak
KEYCLOAK_PORT=8080
KC_HOSTNAME=localhost
```

Or in **keycloak-secrets** in the **k8s/keycloak/deployment.yml** path:

```yml
apiVersion: v1
kind: Secret
metadata:
  name: keycloak-secrets
type: Opaque
stringData:
  KEYCLOAK_ADMIN: "keycloak"
  KEYCLOAK_ADMIN_PASSWORD: "keycloak"
  KC_HOSTNAME: "localhost"
```

## Docker Compose Services Overview

Keyclaok service in docker compose runs in **development mode** :

```yml
command: start-dev --features=token-exchange
```

to run it in **production mode** change the following command to this and provide required certs:

```yml
command: start --https-certificate-file=/certs/tls.pem --https-certificate-key-file=/certs/tls.pem --http-port=8443
```

## Adjust Settings

### Step 1: Login to Keycloak Admin Console

Open the Keycloak Admin Console in your browser:
http://localhost:8080/

### Step 2: Create a Realm

1. In the top-left dropdown, click **Create Realm**
2. Set:
   - **Realm Name:** `test`
3. Click **Create**

> This realm will be used for both clients and users.

---

### Step 3: Create a Client Inside the Realm

1. Go to **Clients**
2. Click **Create client**
3. Set:
   - **Client ID:** `test`
   - **Client Type:** `OpenID Connect`
4. Click **Next** and **Save**

---

### Step 4: Create a Client Role (`staff`)

1. Open the created client (`test`)
2. Go to **Roles**
3. Click **Create role**
4. Set:
   - **Role Name:** `staff`
5. Save the role

> This role can later be embedded into JWT tokens and used for authorization.

---

### Step 5: Configure Client Settings

Open the **Settings** tab of the client and configure:

#### Basic Settings
- **Client Authentication:** `ON`
- **Standard Flow Enabled:** `OFF`
- **Direct Access Grants Enabled:** `ON`

#### Advanced Settings
1. Go to **Advanced**
2. Configure token lifetimes as needed, for example:
   - **Access Token Lifespan:** `5m` or `10m`
   - **Refresh Token Lifespan:** based on your security policy

Save the changes.

---

### Step 6: Get Client Secret

1. Open the client
2. Go to **Credentials**
3. Copy the **Client Secret**

This value will be used in the **users service** `.env` file.

---

### Step 7: Create a User

1. Go to **Users**
2. Click **Create new user**
3. Set:
   - **Username:** `testuser`
   - **Enabled:** `ON`
   - **Email Verified:** `ON`
4. Click **Create**

---

### Step 8: Set User Password

1. Open the user
2. Go to **Credentials**
3. Set a password:
   - Disable **Temporary**
4. Save

---

### Step 10: Configure `.env` File for Users Service

Based on the above configuration, set the following environment variables in the **users service**:

```env
KEYCLOAK_SERVER_URL='http://keycloak:8080'
KEYCLOAK_CLIENT_ID='test'
KEYCLOAK_CLIENT_SECRET_KEY='<your-secret>'
KEYCLOAK_REALM_NAME='test'
KEYCLOAK_USER_REALM_NAME='test'
KEYCLOAK_USERNAME='testuser'
KEYCLOAK_PASSWORD='testuser'
```