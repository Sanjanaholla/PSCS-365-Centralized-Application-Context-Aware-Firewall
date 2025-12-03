const axios = require('axios');
const fs = require('fs');
const https = require('https');

// --- WARNING: This is conceptual code for secure, server-to-server communication ---
// You must have a full Node.js environment setup (npm init, npm install axios) 
// and valid certificate files to run this successfully.

// --- mTLS Certificate Paths ---
// You must generate these certificates (client.crt, client.key) and trust 
// the server's CA (server_ca.crt) in a real mTLS setup.
const CLIENT_CERT_PATH = './certs/client.crt'; 
const CLIENT_KEY_PATH = './certs/client.key';
const SERVER_CA_PATH = './certs/server_ca.crt'; 


// 1. Create a custom HTTPS agent for mTLS
try {
    var httpsAgent = new https.Agent({
        key: fs.readFileSync(CLIENT_KEY_PATH),
        cert: fs.readFileSync(CLIENT_CERT_PATH),
        ca: fs.readFileSync(SERVER_CA_PATH)
    });
} catch (e) {
    console.warn("mTLS Agent Warning: Certificate files not found. This client requires certificates to run.");
    // Create a fallback agent for demonstration if files are missing
    var httpsAgent = new https.Agent({ rejectUnauthorized: false }); 
}


// Function to send the JSON payload securely
const pushPolicyToFastAPI = async (policyPayload) => {
    // Note: This URL must be the reverse proxy (e.g., Nginx) that handles mTLS, not the direct FastAPI URL.
    const url = 'https://api.yourdomain.com/api/v1/policies'; 

    console.log(`Attempting secure policy push to: ${url}`);
    
    try {
        const response = await axios.post(
            url, 
            policyPayload, 
            {
                // 2. Attach the mTLS agent to the request
                httpsAgent: httpsAgent,
                headers: {
                    'Content-Type': 'application/json',
                }
            }
        );

        console.log('Policy successfully pushed (Status: 200/201)');
        console.log('Response:', response.data);

    } catch (error) {
        console.error('\n--- mTLS Connection Error ---');
        console.error('FastAPI/Reverse Proxy may not be running, or certificates are invalid.');
        console.error(error.message);
    }
};

// --- Example Usage ---
const newPolicy = {
    app_name: "NodeJS Client Tool",
    protocol: "ICMP",
    port: 0, // ICMP doesn't use ports, but using 0 for structure
    action: "DENY"
};

// pushPolicyToFastAPI(newPolicy); 
console.log("This script is a conceptual guide. Uncomment 'pushPolicyToFastAPI(newPolicy);' to run.");