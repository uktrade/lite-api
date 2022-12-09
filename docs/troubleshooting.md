## Troubleshooting

### Known issues when running with Docker

  - If you are running the service while also connected to the DIT VPN, there can be an issue where the caseworker frontend will not connect to SSO, as the default subnet used by the Docker daemon overlaps with the subnet used by the VPN. If you need to run the service while connected to the VPN, you may need to update your Docker config locally to change the `default-address-pools` option. Some devs have had success with adding the following to their Docker json config (requires restart):
  ```
  "default-address-pools": [
    {
      "base": "10.10.0.0/16",
      "size": 24
    }
  ],
  ```
