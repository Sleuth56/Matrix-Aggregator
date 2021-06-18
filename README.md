# Matrix Aggregator Skill

## Installation with Docker/Podman
1. Clone the repo. `git clone https://github.com/Sleuth56/Matrix_Aggregator_Skill.git`
2. change directory into it. `cd Matrix_Aggregator_Skill`
3. Rename `configuration.yaml.default` to `configuration.yaml`. `mv configuration.yaml.default configuration.yaml`
4. Make a matrix account on a server. And put the Account name, password, and device ID into the configuration file.
5. Edit `configuration.yaml` with the rooms to aggregate the messages into.
6. Start the bot! `docker-compose up -d`


## Roadmap
- [x] Edits
- [x] Multi-line messages
- [ ] Aggregating to multiple rooms
- [ ] Deletions
- [ ] Breakout !send and !preview into their own matchers
- [ ] Add more things than just $user said
- [ ] More/Better logging
- [ ] Reactions?