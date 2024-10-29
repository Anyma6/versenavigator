import * as core from '@actions/core';
import * as github from '@actions/github';
import fetch from 'node-fetch';

async function run() {
  try {
    const context = github.context;
    const { owner, repo } = context.repo;
    const pull_request_number = context.payload.pull_request.number;

    // Domini da escludere
    const exceptionDomains = ['discord.com','robertsspaceindustries.com']; 
    const readmeUrl = `https://raw.githubusercontent.com/${owner}/${repo}/main/README.md`;

    // Recupero il README.md
    const response = await fetch(readmeUrl);
    if (!response.ok) {
      throw new Error(`Could not fetch README.md: ${response.statusText}`);
    }
    const readmeContent = await response.text();

    // Estrazione dei link dal README.md
    const existingLinks = extractLinks(readmeContent);

    // Recupero il contenuto della PR
    const { data: { body } } = await github.rest.pulls.get({
      owner,
      repo,
      pull_number: pull_request_number,
    });

    // Estrazione dei link dal body della PR
    const prLinks = extractLinks(body);

    const duplicates = prLinks.filter(link => {
      const domain = new URL(link).hostname;
      return existingLinks.includes(link) && !exceptionDomains.includes(domain);
    });

    // Se ci sono duplicati, invia un commento
    if (duplicates.length > 0) {
      const comment = `⚠️ Attenzione: i seguenti link sono già presenti nel README.md:\n\n${duplicates.join('\n')}`;
      await github.rest.issues.createComment({
        owner,
        repo,
        issue_number: pull_request_number,
        body: comment,
      });
    }

  } catch (error) {
    core.setFailed(error.message);
  }
}

function extractLinks(text) {
  const urlRegex = /(https?:\/\/[^\s]+)/g;
  return text.match(urlRegex) || [];
}

// Esegui la funzione
run();
