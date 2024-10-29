const fs = require('fs');
const core = require('@actions/core');
const github = require('@actions/github');

// Funzione per caricare i link dal README.md
function loadLinks() {
  const readme = fs.readFileSync('README.md', 'utf8');
  const regex = /\bhttps?:\/\/\S+/gi;
  return readme.match(regex);
}

// Funzione per caricare i link dalla pull request
async function loadPullRequestLinks(octokit, context) {
  const prNumber = context.payload.pull_request.number;
  const { data: prFiles } = await octokit.pulls.listFiles({
    owner: context.repo.owner,
    repo: context.repo.repo,
    pull_number: prNumber,
  });

  const links = [];
  for (const file of prFiles) {
    if (file.filename.endsWith('.md')) {
      const content = fs.readFileSync(file.filename, 'utf8');
      const fileLinks = content.match(/\bhttps?:\/\/\S+/gi);
      if (fileLinks) {
        links.push(...fileLinks);
      }
    }
  }
  return links;
}

// Funzione per controllare i duplicati
function checkDuplicates(existingLinks, newLinks, exceptions = []) {
  const domains = new Set(existingLinks.map(link => new URL(link).hostname));
  const duplicates = newLinks.filter(link => {
    const hostname = new URL(link).hostname;
    return domains.has(hostname) && !exceptions.includes(hostname);
  });
  return duplicates;
}

// Funzione per inviare un commento alla pull request
async function postComment(octokit, context, message) {
  const prNumber = context.payload.pull_request.number;
  await octokit.issues.createComment({
    owner: context.repo.owner,
    repo: context.repo.repo,
    issue_number: prNumber,
    body: message,
  });
}

(async () => {
  try {
    const context = github.context;
    const octokit = github.getOctokit(process.env.GITHUB_TOKEN);

    const existingLinks = loadLinks();
    const newLinks = await loadPullRequestLinks(octokit, context);
    const exceptions = ['discord.com', 'robertsspaceindustries.com']; // Specifica le eccezioni direttamente qui

    const duplicates = checkDuplicates(existingLinks, newLinks, exceptions);
    if (duplicates.length > 0) {
      const message = `⚠️ Found duplicate links:\n\n${duplicates.join('\n')}\n\nPlease review the pull request and remove duplicate links.`;
      await postComment(octokit, context, message);
      core.setFailed(message);
    } else {
      core.info('No duplicate links found.');
    }
  } catch (error) {
    core.setFailed(error.message);
  }
})();
