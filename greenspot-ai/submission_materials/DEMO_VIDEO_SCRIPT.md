# 🎬 GreenSpot AI - 2-Minute Demo Video Script

**Tips for recording:**
* Use OBS or Loom to record your screen and camera.
* Keep the pacing upbeat. 
* Don't worry about being perfect; passion matters more!

---

### [0:00 - 0:15] Introduction (Visual: Open the 3D Globe Web Dashboard)
* **Action:** Slowly drag the 3D globe to spin it while you speak. Switch the view mode to "Carbon Emissions" (so the red and green dots glow).
* **Script:** *"Hi judges! We are the team behind GreenSpot AI. Right now, companies are spending millions on AI training, defaulting to regions like US-East-1. They pay full price and burn coal-powered electricity, while near-zero-carbon, 70% cheaper spot instances sit completely idle across the globe."*

### [0:15 - 0:45] The Insight (Visual: Scroll down to the Pareto Arbitrage cards)
* **Action:** Scroll down the landing page to show the "Two variables fluctuate" section. Hover over the regions (Stockholm, Montreal, Virginia).
* **Script:** *"We realized that Spot Pricing and Grid Carbon Intensity fluctuate independently every hour. So, we built a Pareto Arbitrage Engine. GreenSpot maps live cloud pricing against real-time grid carbon data. As you can see, our backend gives Stockholm a 98/100 score for being incredibly cheap and green, while Virginia gets a 45."*

### [0:45 - 1:15] The Terminal & Resilience (Visual: Open terminal, run the CLI)
* **Action:** Open your terminal side-by-side with the code editor. Run `greenspot radar` and then `greenspot run --task "python train.py"`. Then show the `checkpoint.py` code.
* **Script:** *"But running on cheap Spot instances means you get preempted. Our platform includes a Resilience Runtime. We actively monitor AWS for 2-minute interruption warnings. Using our simple `@checkpoint_protect` decorator, if AWS kills your instance, GreenSpot instantly flushes your ML weights to S3 and restarts the job in the next best region."*

### [1:15 - 1:45] The Green Receipt (Visual: Show the JSON/HTML receipt output)
* **Action:** Show the terminal output of a successful run, highlighting the "Carbon Avoided" and "Money Saved" statistics.
* **Script:** *"When the job finishes, GreenSpot generates a cryptographic ESG receipt. It proves exactly how much money and carbon you saved by letting us route your workload dynamically."*

### [1:45 - 2:00] Conclusion (Visual: Scroll back up to the spinning globe)
* **Action:** Switch the globe layer to "Compute Demand". 
* **Script:** *"GreenSpot AI proves that you don't have to choose between cutting cloud costs and saving the planet. You can do both. Thanks for watching, and check out our GitHub repo!"*
