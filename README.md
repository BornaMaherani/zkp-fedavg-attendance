# Hybrid ZKP-FedAvg Attendance System

A decentralized, privacy-preserving blockchain attendance system designed for educational environments. This project combines **Zero-Knowledge Proofs (ZKP)** and **Federated Learning (FedAvg)** in an Off-chain/On-chain hybrid architecture.

## Overview
Traditional centralized attendance systems suffer from single points of failure, lack of trust, and potential for data tampering. Storing everything directly on a blockchain solves these issues but introduces high gas costs and scalability problems.

This system resolves this by performing the heavy computations and privacy-sensitive operations **Off-chain** (in Python), while only storing the essential proofs, session hashes, and IPFS CIDs **On-chain** (via Smart Contracts).

## Key Features
- **Privacy-Preserving Verification**: Students prove their local network and device state is stable enough for participation without ever revealing their raw parameters to the server using ZKP.
- **Smart Candidate Selection**: A Greedy algorithm scores students based on historical participation and AI-predicted likelihood of attendance to select optimal participants.
- **Federated Learning**: The system continuously improves its attendance prediction model (a multi-layer perceptron) by training locally on student devices and aggregating the weights via FedAvg.
- **Cheating Mitigation**: Fully resistant to malicious nodes trying to spoof readiness without a valid ZKP.
- **Gas Optimized**: Heavy data and the global AI model are stored on IPFS, with only the content hashes anchored to the smart contract.

## Architecture
- **Coordinator (Server)**: Orchestrates the session, evaluates global AI models, verifies ZKP proofs, runs the Greedy selection algorithm, performs FedAvg, and talks to Web3/IPFS.
- **StudentNode (Client)**: Simulates local devices, calculates prediction errors locally, generates ZKP readiness proofs, signs attendance challenges, and trains the AI model locally.
- **Simulator**: Capable of generating gaussian noise to simulate stable/unstable network conditions for $N$ students, including a "Cheat Mode" to benchmark the effectiveness of the ZKP security layer.

## Requirements
- Python 3.8+
- PyTorch
- eth_account
- Node.js (for SnarkJS verification)

## Structure
- `src/server/`: Contains Coordinator, Metrics Logger, IPFS & Web3 Manager mocks, and Global Model logic.
- `src/client/`: Contains StudentNode, Signer, and Local Model training logic.
- `src/simulator/`: Simulates behavioral profiling and gaussian noise.
- `zkp/`: Zero-Knowledge Proof circuitry and verification scripts.
- `tests/`: Automated scenario tests (Proposed, Random, No-ZKP).

## Usage
Run the fully automated evaluation test (Phase 5) to observe the system across 120 simulated sessions (40 sessions for 3 different scenarios):
```bash
python tests/test_phase5.py
```
This script will produce `evaluation_metrics.csv` along with comparative visualization graphs (`accuracy_comparison.png`, `mse_comparison.png`).
